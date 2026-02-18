"""
Chat route module for MediBot.
Handles /chat, /v1/chat, /chat/stream, and /generate-image endpoints.
"""

import base64
import hashlib
import json
import uuid
import time
import traceback

from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from aws_lambda_powertools import Logger

from models.request_models import ChatRequest, ImageRequest
from models.response_models import ChatResponse, StepImage, ImageResponse
from dependencies import get_optional_user, get_client_info

from gemini_client import (
    invoke_llm,
    invoke_llm_streaming,
    generate_image,
    generate_all_step_images,
    extract_treatment_steps,
    should_generate_images,
    detect_medical_topic,
    LLM_MODEL_ID,
)
from model_router import get_model_for_query, classify_query_complexity
from response_cache import get_cached_response, cache_response
from translation import (
    translate_to_english,
    translate_from_english,
    detect_language,
    SUPPORTED_LANGUAGES,
)
from chat_history import save_chat
from health_profile import get_context_summary
from report_analyzer import extract_facts_from_chat
from guest_tracking import check_guest_limit, increment_guest_message
from audit_logging import log_guest_event
from monitoring import record_security_event as record_security_metric
from llm_safety import check_input_safety, check_output_safety

logger = Logger(service="medibot")
router = APIRouter()


def _should_inject_health_context(
    query: str,
    has_attachments: bool,
    has_history: bool,
) -> bool:
    """
    Inject profile context only for medically meaningful turns.

    Skip on first-turn greetings/chitchat to avoid over-medicalized replies
    like "Hi" -> long clinical context response.
    """
    if has_attachments or has_history:
        return True
    return classify_query_complexity(query, has_attachments=False) != "simple"


@router.post("/chat", response_model=ChatResponse)
@router.post("/v1/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    user_info: Optional[dict] = Depends(get_optional_user),
    client_info: dict = Depends(get_client_info),
):
    """
    Process a medical question with in-depth research and step-by-step visual instructions.

    Features:
    - Thorough medical research using Gemini
    - Extracts treatment steps from the response
    - Generates an image for EACH step (soft limit: 10)
    - All images are 512x512 resolution
    - Conversational, helpful responses
    - Saves chat to DynamoDB if authenticated
    - Request tracing via request_id
    """
    request_id = str(uuid.uuid4())[:8]
    request_start = time.time()
    logger.info("Request started", request_id=request_id)

    try:
        return await _handle_chat(request, background_tasks, user_info, client_info, request_id, request_start)
    except HTTPException:
        raise  # Let FastAPI handle known HTTP exceptions
    except Exception as e:
        logger.error(
            "Unhandled exception in /chat",
            request_id=request_id,
            error=str(e),
            traceback=traceback.format_exc(),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {type(e).__name__}: {str(e)[:200]}",
        )


async def _handle_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    user_info: Optional[dict],
    client_info: dict,
    request_id: str,
    request_start: float,
):
    """Inner implementation of /chat endpoint for clean error boundaries."""

    query = request.query.strip()
    language = request.language

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Phase 4: LLM Safety - Input validation (prompt injection detection)
    input_safe, sanitized_query, fallback_response = check_input_safety(query)
    if not input_safe:
        logger.warning("Blocked potentially unsafe input", request_id=request_id)
        record_security_metric("suspicious")
        return ChatResponse(
            answer=fallback_response or "I'm sorry, but I can't process that request.",
            original_query=query,
            detected_language="en",
            topic=None,
            step_images=None,
            steps_count=0,
        )
    query = sanitized_query

    # Extract client info
    ip_address = client_info["ip_address"]
    client_user_agent = client_info["user_agent"]
    client_fingerprint = client_info["fingerprint"]

    # Phase 3: Guest trial enforcement for unauthenticated users
    if not user_info:
        guest_status = check_guest_limit(
            ip_address=ip_address,
            user_agent=client_user_agent,
            fingerprint=client_fingerprint,
        )

        if not guest_status["allowed"]:
            log_guest_event(
                guest_id=guest_status["guest_id"],
                ip_address=ip_address,
                action="limit_reached",
            )
            logger.warning("Guest limit reached", guest_id=guest_status["guest_id"])
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Guest trial limit reached. Please sign up for unlimited access.",
                    "limit": guest_status["limit"],
                    "message_count": guest_status["message_count"],
                },
            )

        increment_result = increment_guest_message(
            ip_address=ip_address,
            user_agent=client_user_agent,
            fingerprint=client_fingerprint,
            query=query[:100],
        )

        log_guest_event(
            guest_id=increment_result["guest_id"],
            ip_address=ip_address,
            action="chat",
            details={"remaining": increment_result["remaining"]},
        )

        logger.info(
            "Guest chat",
            guest_id=increment_result["guest_id"][:12],
            remaining=increment_result["remaining"],
        )

    # Detect input language and translate to English if needed
    detected_lang = "en"
    try:
        detected_lang = detect_language(query)
    except Exception as e:
        logger.warning(
            "Language detection failed, defaulting to English",
            request_id=request_id,
            error=str(e),
        )
    english_query = query

    if detected_lang != "en":
        try:
            english_query, _ = translate_to_english(query, detected_lang)
        except Exception as e:
            logger.warning(
                "Translation to English failed, using original query",
                request_id=request_id,
                error=str(e),
                detected_language=detected_lang,
            )
            english_query = query

    has_attachments = bool(request.attachments and len(request.attachments) > 0)
    has_history = bool(request.conversation_history)

    # Build context from conversation history if provided
    context = ""
    if has_history:
        context = "\n".join(
            [
                f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
                for msg in request.conversation_history[-4:]
            ]
        )

    # Phase 2.5: Inject health context for personalized RAG
    health_context = ""
    if user_info and _should_inject_health_context(
        english_query, has_attachments=has_attachments, has_history=has_history
    ):
        health_context = get_context_summary(user_info["user_id"])
        if health_context:
            logger.info("Injecting health context", user_id=user_info["user_id"][:8])
            context = health_context + "\n" + context

    # Process file attachments if present
    response = None
    if request.attachments and len(request.attachments) > 0:
        logger.info("Processing attachments", count=len(request.attachments))

        from gemini_client import invoke_llm_with_files
        from report_analyzer import get_report_from_s3

        file_parts = []
        report_tasks = []

        for att in request.attachments:
            try:
                if att.s3_key:
                    logger.info("Processing S3 attachment", key=att.s3_key)
                    file_bytes = get_report_from_s3(att.s3_key)
                    if not file_bytes:
                        logger.error("Failed to fetch S3 attachment", key=att.s3_key)
                        continue

                    file_parts.append(
                        {
                            "data": file_bytes,
                            "mime_type": att.content_type,
                            "filename": att.filename,
                        }
                    )

                    if att.type == "pdf" and user_info:
                        report_tasks.append(att.s3_key)

                elif att.data:
                    file_bytes = base64.b64decode(att.data)
                    file_parts.append(
                        {
                            "data": file_bytes,
                            "mime_type": att.content_type,
                            "filename": att.filename,
                        }
                    )
            except Exception as e:
                logger.error(
                    "Failed to process attachment",
                    filename=att.filename,
                    error=str(e),
                )

        if file_parts:
            response = await run_in_threadpool(
                invoke_llm_with_files,
                english_query,
                file_parts,
                context,
                request.thinking_mode,
            )

            # Improvement 1.3: Background report analysis (was no-op pass before)
            if report_tasks and user_info:
                from report_analyzer import analyze_report

                for s3_key in report_tasks:
                    logger.info("Triggering background report analysis", key=s3_key)
                    background_tasks.add_task(
                        analyze_report, s3_key, user_info["user_id"]
                    )

    # Standard LLM call (no attachments) — with cache + model routing
    if not response:
        # Check response cache first
        cached = None if has_attachments else get_cached_response(english_query)

        if cached:
            response = cached["response"]
            logger.info("Cache HIT", request_id=request_id)
        else:
            # Intelligent model routing
            selected_model = get_model_for_query(
                english_query, has_attachments=has_attachments
            )

            logger.info(
                "Processing query",
                request_id=request_id,
                query=english_query[:50],
                thinking_mode=request.thinking_mode,
                model=selected_model,
            )
            llm_start = time.time()
            response = await run_in_threadpool(
                invoke_llm,
                english_query,
                context,
                1536,
                0.7,
                request.thinking_mode,
                selected_model,
            )
            llm_duration_ms = int((time.time() - llm_start) * 1000)
            logger.info("LLM completed", request_id=request_id, duration_ms=llm_duration_ms)

            # Fallback: if routed model failed, retry with default model
            if not response and selected_model != LLM_MODEL_ID:
                logger.warning(
                    "Routed model failed, retrying with default",
                    request_id=request_id,
                    failed_model=selected_model,
                    fallback_model=LLM_MODEL_ID,
                )
                llm_start = time.time()
                response = await run_in_threadpool(
                    invoke_llm,
                    english_query,
                    context,
                    1536,
                    0.7,
                    request.thinking_mode,
                    LLM_MODEL_ID,
                )
                llm_duration_ms = int((time.time() - llm_start) * 1000)
                logger.info("LLM fallback completed", request_id=request_id, duration_ms=llm_duration_ms)

            # Cache the response (non-blocking, best-effort)
            if response and not has_attachments:
                topic_for_cache = detect_medical_topic(english_query)
                try:
                    cache_response(english_query, response, topic=topic_for_cache or "")
                except Exception:
                    pass  # Non-fatal

    if not response:
        logger.error("LLM failed to respond", request_id=request_id)
        raise HTTPException(status_code=500, detail="Failed to get response from AI")

    # Phase 4: LLM Safety - Output validation
    output_safe, sanitized_response, output_fallback = check_output_safety(response)
    if not output_safe:
        logger.warning("Blocked unsafe output", request_id=request_id)
        record_security_metric("suspicious")
        target_lang = SUPPORTED_LANGUAGES.get(language, "en")
        fallback = output_fallback or "I'm sorry, but I can't provide that response."
        if target_lang != "en":
            fallback = translate_from_english(fallback, target_lang)
        return ChatResponse(
            answer=fallback,
            original_query=query,
            detected_language=detected_lang,
            topic=None,
            step_images=None,
            steps_count=0,
        )

    response = sanitized_response

    # Translate response back if needed
    final_response = response
    target_lang = SUPPORTED_LANGUAGES.get(language, "en")

    if target_lang != "en":
        try:
            final_response = translate_from_english(response, target_lang)
        except Exception as e:
            logger.warning(
                "Translation from English failed, returning English response",
                request_id=request_id,
                error=str(e),
                target_language=target_lang,
            )
            final_response = response

    # Detect topic
    topic = detect_medical_topic(english_query)

    # Generate step-by-step images
    step_images_list = None
    all_images = []
    primary_image = None

    should_generate_step_images = False
    if request.generate_images:
        try:
            should_generate_step_images = should_generate_images(english_query, response)
        except Exception as e:
            logger.warning(
                "Image generation decision failed; skipping step images",
                request_id=request_id,
                error=str(e),
            )

    if should_generate_step_images:
        try:
            steps = extract_treatment_steps(response)
        except Exception as e:
            logger.error(
                "Failed to extract treatment steps; continuing without images",
                request_id=request_id,
                error=str(e),
            )
            steps = []
        logger.info("Extracted treatment steps", count=len(steps))

        if steps:
            # Improvement 3.3: Use SHA-256 instead of MD5
            query_hash = hashlib.sha256(english_query.encode()).hexdigest()[:12]

            logger.info(
                "Generating step-aligned visual guides",
                request_id=request_id,
                steps_count=len(steps),
            )

            elapsed_seconds = time.time() - request_start
            image_gen_start = time.time()
            try:
                step_images_data = await run_in_threadpool(
                    generate_all_step_images, steps, english_query, query_hash,
                    elapsed_seconds,
                )
            except Exception as e:
                logger.error(
                    "Step image generation failed; continuing without images",
                    request_id=request_id,
                    error=str(e),
                )
                step_images_data = []
            image_gen_duration_ms = int((time.time() - image_gen_start) * 1000)
            failed_count = sum(1 for s in step_images_data if s.get("image_failed"))
            logger.info(
                "Image generation completed",
                request_id=request_id,
                duration_ms=image_gen_duration_ms,
                total_images=len(step_images_data),
                failed_images=failed_count,
            )

            step_images_list = []
            for step_data in step_images_data:
                image_url = step_data.get("image_url")
                image_base64 = step_data.get("image")

                step_images_list.append(
                    StepImage(
                        step_number=step_data["step_number"],
                        title=step_data["title"],
                        description=step_data["description"],
                        image_prompt=step_data.get("image_prompt"),
                        image=image_base64 if not image_url else None,
                        image_url=image_url,
                        s3_key=step_data.get("s3_key"),
                        is_composite=step_data.get("is_composite", False),
                        panel_index=step_data.get("panel_index"),
                        image_failed=step_data.get("image_failed", False),
                        fallback_text=step_data.get("fallback_text"),
                    )
                )

                if image_url:
                    all_images.append(image_url)
                elif image_base64:
                    all_images.append(image_base64)

            if all_images:
                primary_image = all_images[0]

    # Improvement 3.2: Move save_chat and extract_facts to BackgroundTasks
    if user_info:
        step_images_data = (
            [
                {
                    "step_number": img.step_number,
                    "title": img.title,
                    "description": img.description,
                    "image_url": img.image_url,
                    "s3_key": img.s3_key,
                    "image_failed": img.image_failed,
                    "fallback_text": img.fallback_text,
                }
                for img in step_images_list
            ]
            if step_images_list
            else []
        )

        attachments_data = (
            [
                {
                    "filename": att.filename,
                    "type": att.type,
                    "content_type": att.content_type,
                }
                for att in (request.attachments or [])
            ]
            if request.attachments
            else []
        )

        # Save chat in background (non-blocking)
        background_tasks.add_task(
            save_chat,
            user_id=user_info["user_id"],
            query=query,
            response=final_response,
            images=all_images if all_images else [],
            topic=topic,
            language=language,
            step_images=step_images_data,
            attachments=attachments_data,
        )

        # Extract health facts in background (non-blocking)
        background_tasks.add_task(
            _extract_facts_background,
            user_info["user_id"],
            query,
            final_response,
        )

    # Log total request duration
    total_duration_ms = int((time.time() - request_start) * 1000)
    logger.info(
        "Request completed",
        request_id=request_id,
        total_duration_ms=total_duration_ms,
        steps_count=len(step_images_list) if step_images_list else 0,
    )

    return ChatResponse(
        answer=final_response,
        original_query=query,
        detected_language=detected_lang,
        topic=topic,
        step_images=step_images_list,
        steps_count=len(step_images_list) if step_images_list else 0,
        image=primary_image,
        images=all_images if all_images else None,
    )


def _extract_facts_background(user_id: str, query: str, response: str):
    """Background task to extract health facts from chat."""
    try:
        extracted = extract_facts_from_chat(user_id, query, response)
        if extracted:
            logger.info("Extracted facts", facts=extracted)
    except Exception as e:
        logger.error("Failed to extract facts", error=str(e))


@router.post("/generate-image", response_model=ImageResponse)
async def create_image(request: ImageRequest):
    """Generate a single medical illustration."""
    image_bytes = generate_image(
        request.prompt, width=request.width, height=request.height
    )

    if not image_bytes:
        raise HTTPException(status_code=500, detail="Failed to generate image")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    return ImageResponse(image=image_b64, prompt=request.prompt)


# ============================================
# SSE Streaming Endpoint
# ============================================
@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    user_info: Optional[dict] = Depends(get_optional_user),
    client_info: dict = Depends(get_client_info),
):
    """
    Stream a medical response as Server-Sent Events.

    Events:
    - event: token  — text chunk from LLM
    - event: metadata — topic, detected language
    - event: step_images — JSON array of step images (after text completes)
    - event: done — stream end
    - event: error — error info
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Safety check
    input_safe, sanitized_query, fallback_response = check_input_safety(query)
    if not input_safe:
        async def error_stream():
            yield f"event: error\ndata: {json.dumps({'message': fallback_response})}\n\n"
            yield "event: done\ndata: {}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    query = sanitized_query

    # Language detection
    detected_lang = "en"
    try:
        detected_lang = detect_language(query)
    except Exception as e:
        logger.warning("Stream language detection failed", error=str(e))
    english_query = query
    if detected_lang != "en":
        try:
            english_query, _ = translate_to_english(query, detected_lang)
        except Exception as e:
            logger.warning("Stream translation to English failed", error=str(e))
            english_query = query

    # Build context
    context = ""
    has_attachments = bool(request.attachments and len(request.attachments) > 0)
    has_history = bool(request.conversation_history)

    if has_history:
        context = "\n".join(
            f"{'User' if m.get('role')=='user' else 'Assistant'}: {m.get('content','')}"
            for m in request.conversation_history[-4:]
        )
    if user_info and _should_inject_health_context(
        english_query, has_attachments=has_attachments, has_history=has_history
    ):
        hc = get_context_summary(user_info["user_id"])
        if hc:
            context = hc + "\n" + context

    # Model routing
    selected_model = get_model_for_query(english_query, has_attachments=has_attachments)

    # Check cache
    cached = None if has_attachments else get_cached_response(english_query)

    async def event_generator():
        request_start = time.time()
        full_response = ""

        try:
            if cached:
                # Stream cached response in chunks for consistent UX
                text = cached["response"]
                chunk_size = 80
                for i in range(0, len(text), chunk_size):
                    chunk = text[i:i+chunk_size]
                    yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"
                full_response = text
            else:
                # Stream from LLM
                for chunk in invoke_llm_streaming(
                    english_query, context, 1536, 0.7,
                    request.thinking_mode, selected_model
                ):
                    full_response += chunk
                    yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"

                # Cache the response
                if full_response:
                    topic_for_cache = detect_medical_topic(english_query)
                    try:
                        cache_response(english_query, full_response, topic=topic_for_cache or "")
                    except Exception:
                        pass

            if not full_response:
                yield f"event: error\ndata: {json.dumps({'message': 'No response from AI'})}\n\n"
                yield "event: done\ndata: {}\n\n"
                return

            # Output safety
            output_safe, sanitized, fallback = check_output_safety(full_response)
            if not output_safe:
                yield f"event: error\ndata: {json.dumps({'message': fallback or 'Response blocked by safety filter'})}\n\n"
                yield "event: done\ndata: {}\n\n"
                return

            # Translate if needed
            target_lang = SUPPORTED_LANGUAGES.get(request.language, "en")
            final_response = sanitized
            if target_lang != "en":
                try:
                    final_response = translate_from_english(sanitized, target_lang)
                except Exception as e:
                    logger.warning("Stream translation from English failed", error=str(e))
                    final_response = sanitized

            # Metadata event
            topic = detect_medical_topic(english_query)
            yield f"event: metadata\ndata: {json.dumps({'topic': topic, 'detected_language': detected_lang})}\n\n"

            # Generate images if requested
            should_generate_stream_images = False
            if request.generate_images:
                try:
                    should_generate_stream_images = should_generate_images(english_query, sanitized)
                except Exception as e:
                    logger.warning("Stream image generation decision failed", error=str(e))

            if should_generate_stream_images:
                try:
                    steps = extract_treatment_steps(sanitized)
                except Exception as e:
                    logger.error("Stream step extraction failed", error=str(e))
                    steps = []
                if steps:
                    elapsed = time.time() - request_start
                    query_hash = hashlib.sha256(english_query.encode()).hexdigest()[:12]
                    try:
                        step_images_data = await run_in_threadpool(
                            generate_all_step_images, steps, english_query, query_hash, elapsed
                        )
                    except Exception as e:
                        logger.error("Stream image generation failed", error=str(e))
                        step_images_data = []
                    yield f"event: step_images\ndata: {json.dumps(step_images_data, default=str)}\n\n"

            yield "event: done\ndata: {}\n\n"

        except Exception as e:
            logger.error("Stream error", error=str(e))
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
            yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ============================================
# Admin: Cache Warming
# ============================================
@router.post("/admin/warm-cache")
async def warm_cache_endpoint():
    """Pre-generate and cache responses for common medical queries."""
    from cache_warmer import warm_cache
    results = await run_in_threadpool(warm_cache)
    return results
