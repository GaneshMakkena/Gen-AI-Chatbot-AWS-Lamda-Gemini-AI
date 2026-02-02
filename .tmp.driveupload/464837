"""
Type annotations for ecr service type definitions.

[Documentation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ecr/type_defs/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from mypy_boto3_ecr.type_defs import AttributeTypeDef

    data: AttributeTypeDef = ...
    ```
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from datetime import datetime
from typing import IO, Any, Union

from botocore.response import StreamingBody

from .literals import (
    ArtifactStatusFilterType,
    ArtifactStatusType,
    EncryptionTypeType,
    FindingSeverityType,
    ImageActionTypeType,
    ImageFailureCodeType,
    ImageStatusFilterType,
    ImageStatusType,
    ImageTagMutabilityType,
    LayerAvailabilityType,
    LayerFailureCodeType,
    LifecyclePolicyPreviewStatusType,
    LifecyclePolicyStorageClassType,
    RCTAppliedForType,
    ReplicationStatusType,
    ScanFrequencyType,
    ScanStatusType,
    ScanTypeType,
    SigningStatusType,
    TagStatusType,
    TargetStorageClassType,
    UpstreamRegistryType,
)

if sys.version_info >= (3, 12):
    from typing import Literal, NotRequired, TypedDict
else:
    from typing_extensions import Literal, NotRequired, TypedDict

__all__ = (
    "AttributeTypeDef",
    "AuthorizationDataTypeDef",
    "AwsEcrContainerImageDetailsTypeDef",
    "BatchCheckLayerAvailabilityRequestTypeDef",
    "BatchCheckLayerAvailabilityResponseTypeDef",
    "BatchDeleteImageRequestTypeDef",
    "BatchDeleteImageResponseTypeDef",
    "BatchGetImageRequestTypeDef",
    "BatchGetImageResponseTypeDef",
    "BatchGetRepositoryScanningConfigurationRequestTypeDef",
    "BatchGetRepositoryScanningConfigurationResponseTypeDef",
    "BlobTypeDef",
    "CompleteLayerUploadRequestTypeDef",
    "CompleteLayerUploadResponseTypeDef",
    "CreatePullThroughCacheRuleRequestTypeDef",
    "CreatePullThroughCacheRuleResponseTypeDef",
    "CreateRepositoryCreationTemplateRequestTypeDef",
    "CreateRepositoryCreationTemplateResponseTypeDef",
    "CreateRepositoryRequestTypeDef",
    "CreateRepositoryResponseTypeDef",
    "CvssScoreAdjustmentTypeDef",
    "CvssScoreDetailsTypeDef",
    "CvssScoreTypeDef",
    "DeleteLifecyclePolicyRequestTypeDef",
    "DeleteLifecyclePolicyResponseTypeDef",
    "DeletePullThroughCacheRuleRequestTypeDef",
    "DeletePullThroughCacheRuleResponseTypeDef",
    "DeleteRegistryPolicyResponseTypeDef",
    "DeleteRepositoryCreationTemplateRequestTypeDef",
    "DeleteRepositoryCreationTemplateResponseTypeDef",
    "DeleteRepositoryPolicyRequestTypeDef",
    "DeleteRepositoryPolicyResponseTypeDef",
    "DeleteRepositoryRequestTypeDef",
    "DeleteRepositoryResponseTypeDef",
    "DeleteSigningConfigurationResponseTypeDef",
    "DeregisterPullTimeUpdateExclusionRequestTypeDef",
    "DeregisterPullTimeUpdateExclusionResponseTypeDef",
    "DescribeImageReplicationStatusRequestTypeDef",
    "DescribeImageReplicationStatusResponseTypeDef",
    "DescribeImageScanFindingsRequestPaginateTypeDef",
    "DescribeImageScanFindingsRequestTypeDef",
    "DescribeImageScanFindingsRequestWaitTypeDef",
    "DescribeImageScanFindingsResponseTypeDef",
    "DescribeImageSigningStatusRequestTypeDef",
    "DescribeImageSigningStatusResponseTypeDef",
    "DescribeImagesFilterTypeDef",
    "DescribeImagesRequestPaginateTypeDef",
    "DescribeImagesRequestTypeDef",
    "DescribeImagesResponseTypeDef",
    "DescribePullThroughCacheRulesRequestPaginateTypeDef",
    "DescribePullThroughCacheRulesRequestTypeDef",
    "DescribePullThroughCacheRulesResponseTypeDef",
    "DescribeRegistryResponseTypeDef",
    "DescribeRepositoriesRequestPaginateTypeDef",
    "DescribeRepositoriesRequestTypeDef",
    "DescribeRepositoriesResponseTypeDef",
    "DescribeRepositoryCreationTemplatesRequestPaginateTypeDef",
    "DescribeRepositoryCreationTemplatesRequestTypeDef",
    "DescribeRepositoryCreationTemplatesResponseTypeDef",
    "EncryptionConfigurationForRepositoryCreationTemplateTypeDef",
    "EncryptionConfigurationTypeDef",
    "EnhancedImageScanFindingTypeDef",
    "GetAccountSettingRequestTypeDef",
    "GetAccountSettingResponseTypeDef",
    "GetAuthorizationTokenRequestTypeDef",
    "GetAuthorizationTokenResponseTypeDef",
    "GetDownloadUrlForLayerRequestTypeDef",
    "GetDownloadUrlForLayerResponseTypeDef",
    "GetLifecyclePolicyPreviewRequestPaginateTypeDef",
    "GetLifecyclePolicyPreviewRequestTypeDef",
    "GetLifecyclePolicyPreviewRequestWaitTypeDef",
    "GetLifecyclePolicyPreviewResponseTypeDef",
    "GetLifecyclePolicyRequestTypeDef",
    "GetLifecyclePolicyResponseTypeDef",
    "GetRegistryPolicyResponseTypeDef",
    "GetRegistryScanningConfigurationResponseTypeDef",
    "GetRepositoryPolicyRequestTypeDef",
    "GetRepositoryPolicyResponseTypeDef",
    "GetSigningConfigurationResponseTypeDef",
    "ImageDetailTypeDef",
    "ImageFailureTypeDef",
    "ImageIdentifierTypeDef",
    "ImageReferrerTypeDef",
    "ImageReplicationStatusTypeDef",
    "ImageScanFindingTypeDef",
    "ImageScanFindingsSummaryTypeDef",
    "ImageScanFindingsTypeDef",
    "ImageScanStatusTypeDef",
    "ImageScanningConfigurationTypeDef",
    "ImageSigningStatusTypeDef",
    "ImageTagMutabilityExclusionFilterTypeDef",
    "ImageTypeDef",
    "InitiateLayerUploadRequestTypeDef",
    "InitiateLayerUploadResponseTypeDef",
    "LayerFailureTypeDef",
    "LayerTypeDef",
    "LifecyclePolicyPreviewFilterTypeDef",
    "LifecyclePolicyPreviewResultTypeDef",
    "LifecyclePolicyPreviewSummaryTypeDef",
    "LifecyclePolicyRuleActionTypeDef",
    "ListImageReferrersFilterTypeDef",
    "ListImageReferrersRequestTypeDef",
    "ListImageReferrersResponseTypeDef",
    "ListImagesFilterTypeDef",
    "ListImagesRequestPaginateTypeDef",
    "ListImagesRequestTypeDef",
    "ListImagesResponseTypeDef",
    "ListPullTimeUpdateExclusionsRequestTypeDef",
    "ListPullTimeUpdateExclusionsResponseTypeDef",
    "ListTagsForResourceRequestTypeDef",
    "ListTagsForResourceResponseTypeDef",
    "PackageVulnerabilityDetailsTypeDef",
    "PaginatorConfigTypeDef",
    "PullThroughCacheRuleTypeDef",
    "PutAccountSettingRequestTypeDef",
    "PutAccountSettingResponseTypeDef",
    "PutImageRequestTypeDef",
    "PutImageResponseTypeDef",
    "PutImageScanningConfigurationRequestTypeDef",
    "PutImageScanningConfigurationResponseTypeDef",
    "PutImageTagMutabilityRequestTypeDef",
    "PutImageTagMutabilityResponseTypeDef",
    "PutLifecyclePolicyRequestTypeDef",
    "PutLifecyclePolicyResponseTypeDef",
    "PutRegistryPolicyRequestTypeDef",
    "PutRegistryPolicyResponseTypeDef",
    "PutRegistryScanningConfigurationRequestTypeDef",
    "PutRegistryScanningConfigurationResponseTypeDef",
    "PutReplicationConfigurationRequestTypeDef",
    "PutReplicationConfigurationResponseTypeDef",
    "PutSigningConfigurationRequestTypeDef",
    "PutSigningConfigurationResponseTypeDef",
    "RecommendationTypeDef",
    "RegisterPullTimeUpdateExclusionRequestTypeDef",
    "RegisterPullTimeUpdateExclusionResponseTypeDef",
    "RegistryScanningConfigurationTypeDef",
    "RegistryScanningRuleOutputTypeDef",
    "RegistryScanningRuleTypeDef",
    "RegistryScanningRuleUnionTypeDef",
    "RemediationTypeDef",
    "ReplicationConfigurationOutputTypeDef",
    "ReplicationConfigurationTypeDef",
    "ReplicationConfigurationUnionTypeDef",
    "ReplicationDestinationTypeDef",
    "ReplicationRuleOutputTypeDef",
    "ReplicationRuleTypeDef",
    "RepositoryCreationTemplateTypeDef",
    "RepositoryFilterTypeDef",
    "RepositoryScanningConfigurationFailureTypeDef",
    "RepositoryScanningConfigurationTypeDef",
    "RepositoryTypeDef",
    "ResourceDetailsTypeDef",
    "ResourceTypeDef",
    "ResponseMetadataTypeDef",
    "ScanningRepositoryFilterTypeDef",
    "ScoreDetailsTypeDef",
    "SetRepositoryPolicyRequestTypeDef",
    "SetRepositoryPolicyResponseTypeDef",
    "SigningConfigurationOutputTypeDef",
    "SigningConfigurationTypeDef",
    "SigningConfigurationUnionTypeDef",
    "SigningRepositoryFilterTypeDef",
    "SigningRuleOutputTypeDef",
    "SigningRuleTypeDef",
    "StartImageScanRequestTypeDef",
    "StartImageScanResponseTypeDef",
    "StartLifecyclePolicyPreviewRequestTypeDef",
    "StartLifecyclePolicyPreviewResponseTypeDef",
    "SubjectIdentifierTypeDef",
    "TagResourceRequestTypeDef",
    "TagTypeDef",
    "TransitioningImageTotalCountTypeDef",
    "UntagResourceRequestTypeDef",
    "UpdateImageStorageClassRequestTypeDef",
    "UpdateImageStorageClassResponseTypeDef",
    "UpdatePullThroughCacheRuleRequestTypeDef",
    "UpdatePullThroughCacheRuleResponseTypeDef",
    "UpdateRepositoryCreationTemplateRequestTypeDef",
    "UpdateRepositoryCreationTemplateResponseTypeDef",
    "UploadLayerPartRequestTypeDef",
    "UploadLayerPartResponseTypeDef",
    "ValidatePullThroughCacheRuleRequestTypeDef",
    "ValidatePullThroughCacheRuleResponseTypeDef",
    "VulnerablePackageTypeDef",
    "WaiterConfigTypeDef",
)

class AttributeTypeDef(TypedDict):
    key: str
    value: NotRequired[str]

class AuthorizationDataTypeDef(TypedDict):
    authorizationToken: NotRequired[str]
    expiresAt: NotRequired[datetime]
    proxyEndpoint: NotRequired[str]

class AwsEcrContainerImageDetailsTypeDef(TypedDict):
    architecture: NotRequired[str]
    author: NotRequired[str]
    imageHash: NotRequired[str]
    imageTags: NotRequired[list[str]]
    platform: NotRequired[str]
    pushedAt: NotRequired[datetime]
    lastInUseAt: NotRequired[datetime]
    inUseCount: NotRequired[int]
    registry: NotRequired[str]
    repositoryName: NotRequired[str]

class BatchCheckLayerAvailabilityRequestTypeDef(TypedDict):
    repositoryName: str
    layerDigests: Sequence[str]
    registryId: NotRequired[str]

class LayerFailureTypeDef(TypedDict):
    layerDigest: NotRequired[str]
    failureCode: NotRequired[LayerFailureCodeType]
    failureReason: NotRequired[str]

class LayerTypeDef(TypedDict):
    layerDigest: NotRequired[str]
    layerAvailability: NotRequired[LayerAvailabilityType]
    layerSize: NotRequired[int]
    mediaType: NotRequired[str]

class ResponseMetadataTypeDef(TypedDict):
    RequestId: str
    HTTPStatusCode: int
    HTTPHeaders: dict[str, str]
    RetryAttempts: int
    HostId: NotRequired[str]

class ImageIdentifierTypeDef(TypedDict):
    imageDigest: NotRequired[str]
    imageTag: NotRequired[str]

class BatchGetRepositoryScanningConfigurationRequestTypeDef(TypedDict):
    repositoryNames: Sequence[str]

class RepositoryScanningConfigurationFailureTypeDef(TypedDict):
    repositoryName: NotRequired[str]
    failureCode: NotRequired[Literal["REPOSITORY_NOT_FOUND"]]
    failureReason: NotRequired[str]

BlobTypeDef = Union[str, bytes, IO[Any], StreamingBody]

class CompleteLayerUploadRequestTypeDef(TypedDict):
    repositoryName: str
    uploadId: str
    layerDigests: Sequence[str]
    registryId: NotRequired[str]

class CreatePullThroughCacheRuleRequestTypeDef(TypedDict):
    ecrRepositoryPrefix: str
    upstreamRegistryUrl: str
    registryId: NotRequired[str]
    upstreamRegistry: NotRequired[UpstreamRegistryType]
    credentialArn: NotRequired[str]
    customRoleArn: NotRequired[str]
    upstreamRepositoryPrefix: NotRequired[str]

class EncryptionConfigurationForRepositoryCreationTemplateTypeDef(TypedDict):
    encryptionType: EncryptionTypeType
    kmsKey: NotRequired[str]

ImageTagMutabilityExclusionFilterTypeDef = TypedDict(
    "ImageTagMutabilityExclusionFilterTypeDef",
    {
        "filterType": Literal["WILDCARD"],
        "filter": str,
    },
)

class TagTypeDef(TypedDict):
    Key: str
    Value: str

class EncryptionConfigurationTypeDef(TypedDict):
    encryptionType: EncryptionTypeType
    kmsKey: NotRequired[str]

class ImageScanningConfigurationTypeDef(TypedDict):
    scanOnPush: NotRequired[bool]

class CvssScoreAdjustmentTypeDef(TypedDict):
    metric: NotRequired[str]
    reason: NotRequired[str]

class CvssScoreTypeDef(TypedDict):
    baseScore: NotRequired[float]
    scoringVector: NotRequired[str]
    source: NotRequired[str]
    version: NotRequired[str]

class DeleteLifecyclePolicyRequestTypeDef(TypedDict):
    repositoryName: str
    registryId: NotRequired[str]

class DeletePullThroughCacheRuleRequestTypeDef(TypedDict):
    ecrRepositoryPrefix: str
    registryId: NotRequired[str]

class DeleteRepositoryCreationTemplateRequestTypeDef(TypedDict):
    prefix: str

class DeleteRepositoryPolicyRequestTypeDef(TypedDict):
    repositoryName: str
    registryId: NotRequired[str]

class DeleteRepositoryRequestTypeDef(TypedDict):
    repositoryName: str
    registryId: NotRequired[str]
    force: NotRequired[bool]

class DeregisterPullTimeUpdateExclusionRequestTypeDef(TypedDict):
    principalArn: str

class ImageReplicationStatusTypeDef(TypedDict):
    region: NotRequired[str]
    registryId: NotRequired[str]
    status: NotRequired[ReplicationStatusType]
    failureCode: NotRequired[str]

class PaginatorConfigTypeDef(TypedDict):
    MaxItems: NotRequired[int]
    PageSize: NotRequired[int]
    StartingToken: NotRequired[str]

class WaiterConfigTypeDef(TypedDict):
    Delay: NotRequired[int]
    MaxAttempts: NotRequired[int]

class ImageScanStatusTypeDef(TypedDict):
    status: NotRequired[ScanStatusType]
    description: NotRequired[str]

class ImageSigningStatusTypeDef(TypedDict):
    signingProfileArn: NotRequired[str]
    failureCode: NotRequired[str]
    failureReason: NotRequired[str]
    status: NotRequired[SigningStatusType]

class DescribeImagesFilterTypeDef(TypedDict):
    tagStatus: NotRequired[TagStatusType]
    imageStatus: NotRequired[ImageStatusFilterType]

class DescribePullThroughCacheRulesRequestTypeDef(TypedDict):
    registryId: NotRequired[str]
    ecrRepositoryPrefixes: NotRequired[Sequence[str]]
    nextToken: NotRequired[str]
    maxResults: NotRequired[int]

class PullThroughCacheRuleTypeDef(TypedDict):
    ecrRepositoryPrefix: NotRequired[str]
    upstreamRegistryUrl: NotRequired[str]
    createdAt: NotRequired[datetime]
    registryId: NotRequired[str]
    credentialArn: NotRequired[str]
    customRoleArn: NotRequired[str]
    upstreamRepositoryPrefix: NotRequired[str]
    upstreamRegistry: NotRequired[UpstreamRegistryType]
    updatedAt: NotRequired[datetime]

class DescribeRepositoriesRequestTypeDef(TypedDict):
    registryId: NotRequired[str]
    repositoryNames: NotRequired[Sequence[str]]
    nextToken: NotRequired[str]
    maxResults: NotRequired[int]

class DescribeRepositoryCreationTemplatesRequestTypeDef(TypedDict):
    prefixes: NotRequired[Sequence[str]]
    nextToken: NotRequired[str]
    maxResults: NotRequired[int]

class GetAccountSettingRequestTypeDef(TypedDict):
    name: str

class GetAuthorizationTokenRequestTypeDef(TypedDict):
    registryIds: NotRequired[Sequence[str]]

class GetDownloadUrlForLayerRequestTypeDef(TypedDict):
    repositoryName: str
    layerDigest: str
    registryId: NotRequired[str]

class LifecyclePolicyPreviewFilterTypeDef(TypedDict):
    tagStatus: NotRequired[TagStatusType]

class GetLifecyclePolicyRequestTypeDef(TypedDict):
    repositoryName: str
    registryId: NotRequired[str]

class GetRepositoryPolicyRequestTypeDef(TypedDict):
    repositoryName: str
    registryId: NotRequired[str]

class ImageScanFindingsSummaryTypeDef(TypedDict):
    imageScanCompletedAt: NotRequired[datetime]
    vulnerabilitySourceUpdatedAt: NotRequired[datetime]
    findingSeverityCounts: NotRequired[dict[FindingSeverityType, int]]

class ImageReferrerTypeDef(TypedDict):
    digest: str
    mediaType: str
    size: int
    artifactType: NotRequired[str]
    annotations: NotRequired[dict[str, str]]
    artifactStatus: NotRequired[ArtifactStatusType]

class InitiateLayerUploadRequestTypeDef(TypedDict):
    repositoryName: str
    registryId: NotRequired[str]

LifecyclePolicyRuleActionTypeDef = TypedDict(
    "LifecyclePolicyRuleActionTypeDef",
    {
        "type": NotRequired[ImageActionTypeType],
        "targetStorageClass": NotRequired[Literal["ARCHIVE"]],
    },
)

class TransitioningImageTotalCountTypeDef(TypedDict):
    targetStorageClass: NotRequired[Literal["ARCHIVE"]]
    imageTotalCount: NotRequired[int]

class ListImageReferrersFilterTypeDef(TypedDict):
    artifactTypes: NotRequired[Sequence[str]]
    artifactStatus: NotRequired[ArtifactStatusFilterType]

class SubjectIdentifierTypeDef(TypedDict):
    imageDigest: str

class ListImagesFilterTypeDef(TypedDict):
    tagStatus: NotRequired[TagStatusType]
    imageStatus: NotRequired[ImageStatusFilterType]

class ListPullTimeUpdateExclusionsRequestTypeDef(TypedDict):
    maxResults: NotRequired[int]
    nextToken: NotRequired[str]

class ListTagsForResourceRequestTypeDef(TypedDict):
    resourceArn: str

class VulnerablePackageTypeDef(TypedDict):
    arch: NotRequired[str]
    epoch: NotRequired[int]
    filePath: NotRequired[str]
    name: NotRequired[str]
    packageManager: NotRequired[str]
    release: NotRequired[str]
    sourceLayerHash: NotRequired[str]
    version: NotRequired[str]
    fixedInVersion: NotRequired[str]

class PutAccountSettingRequestTypeDef(TypedDict):
    name: str
    value: str

class PutImageRequestTypeDef(TypedDict):
    repositoryName: str
    imageManifest: str
    registryId: NotRequired[str]
    imageManifestMediaType: NotRequired[str]
    imageTag: NotRequired[str]
    imageDigest: NotRequired[str]

class PutLifecyclePolicyRequestTypeDef(TypedDict):
    repositoryName: str
    lifecyclePolicyText: str
    registryId: NotRequired[str]

class PutRegistryPolicyRequestTypeDef(TypedDict):
    policyText: str

class RecommendationTypeDef(TypedDict):
    url: NotRequired[str]
    text: NotRequired[str]

class RegisterPullTimeUpdateExclusionRequestTypeDef(TypedDict):
    principalArn: str

ScanningRepositoryFilterTypeDef = TypedDict(
    "ScanningRepositoryFilterTypeDef",
    {
        "filter": str,
        "filterType": Literal["WILDCARD"],
    },
)

class ReplicationDestinationTypeDef(TypedDict):
    region: str
    registryId: str

RepositoryFilterTypeDef = TypedDict(
    "RepositoryFilterTypeDef",
    {
        "filter": str,
        "filterType": Literal["PREFIX_MATCH"],
    },
)

class SetRepositoryPolicyRequestTypeDef(TypedDict):
    repositoryName: str
    policyText: str
    registryId: NotRequired[str]
    force: NotRequired[bool]

SigningRepositoryFilterTypeDef = TypedDict(
    "SigningRepositoryFilterTypeDef",
    {
        "filter": str,
        "filterType": Literal["WILDCARD_MATCH"],
    },
)

class StartLifecyclePolicyPreviewRequestTypeDef(TypedDict):
    repositoryName: str
    registryId: NotRequired[str]
    lifecyclePolicyText: NotRequired[str]

class UntagResourceRequestTypeDef(TypedDict):
    resourceArn: str
    tagKeys: Sequence[str]

class UpdatePullThroughCacheRuleRequestTypeDef(TypedDict):
    ecrRepositoryPrefix: str
    registryId: NotRequired[str]
    credentialArn: NotRequired[str]
    customRoleArn: NotRequired[str]

class ValidatePullThroughCacheRuleRequestTypeDef(TypedDict):
    ecrRepositoryPrefix: str
    registryId: NotRequired[str]

class ImageScanFindingTypeDef(TypedDict):
    name: NotRequired[str]
    description: NotRequired[str]
    uri: NotRequired[str]
    severity: NotRequired[FindingSeverityType]
    attributes: NotRequired[list[AttributeTypeDef]]

class ResourceDetailsTypeDef(TypedDict):
    awsEcrContainerImage: NotRequired[AwsEcrContainerImageDetailsTypeDef]

class BatchCheckLayerAvailabilityResponseTypeDef(TypedDict):
    layers: list[LayerTypeDef]
    failures: list[LayerFailureTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

class CompleteLayerUploadResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    uploadId: str
    layerDigest: str
    ResponseMetadata: ResponseMetadataTypeDef

class CreatePullThroughCacheRuleResponseTypeDef(TypedDict):
    ecrRepositoryPrefix: str
    upstreamRegistryUrl: str
    createdAt: datetime
    registryId: str
    upstreamRegistry: UpstreamRegistryType
    credentialArn: str
    customRoleArn: str
    upstreamRepositoryPrefix: str
    ResponseMetadata: ResponseMetadataTypeDef

class DeleteLifecyclePolicyResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    lifecyclePolicyText: str
    lastEvaluatedAt: datetime
    ResponseMetadata: ResponseMetadataTypeDef

class DeletePullThroughCacheRuleResponseTypeDef(TypedDict):
    ecrRepositoryPrefix: str
    upstreamRegistryUrl: str
    createdAt: datetime
    registryId: str
    credentialArn: str
    customRoleArn: str
    upstreamRepositoryPrefix: str
    ResponseMetadata: ResponseMetadataTypeDef

class DeleteRegistryPolicyResponseTypeDef(TypedDict):
    registryId: str
    policyText: str
    ResponseMetadata: ResponseMetadataTypeDef

class DeleteRepositoryPolicyResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    policyText: str
    ResponseMetadata: ResponseMetadataTypeDef

class DeregisterPullTimeUpdateExclusionResponseTypeDef(TypedDict):
    principalArn: str
    ResponseMetadata: ResponseMetadataTypeDef

class GetAccountSettingResponseTypeDef(TypedDict):
    name: str
    value: str
    ResponseMetadata: ResponseMetadataTypeDef

class GetAuthorizationTokenResponseTypeDef(TypedDict):
    authorizationData: list[AuthorizationDataTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

class GetDownloadUrlForLayerResponseTypeDef(TypedDict):
    downloadUrl: str
    layerDigest: str
    ResponseMetadata: ResponseMetadataTypeDef

class GetLifecyclePolicyResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    lifecyclePolicyText: str
    lastEvaluatedAt: datetime
    ResponseMetadata: ResponseMetadataTypeDef

class GetRegistryPolicyResponseTypeDef(TypedDict):
    registryId: str
    policyText: str
    ResponseMetadata: ResponseMetadataTypeDef

class GetRepositoryPolicyResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    policyText: str
    ResponseMetadata: ResponseMetadataTypeDef

class InitiateLayerUploadResponseTypeDef(TypedDict):
    uploadId: str
    partSize: int
    ResponseMetadata: ResponseMetadataTypeDef

class ListPullTimeUpdateExclusionsResponseTypeDef(TypedDict):
    pullTimeUpdateExclusions: list[str]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class PutAccountSettingResponseTypeDef(TypedDict):
    name: str
    value: str
    ResponseMetadata: ResponseMetadataTypeDef

class PutLifecyclePolicyResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    lifecyclePolicyText: str
    ResponseMetadata: ResponseMetadataTypeDef

class PutRegistryPolicyResponseTypeDef(TypedDict):
    registryId: str
    policyText: str
    ResponseMetadata: ResponseMetadataTypeDef

class RegisterPullTimeUpdateExclusionResponseTypeDef(TypedDict):
    principalArn: str
    createdAt: datetime
    ResponseMetadata: ResponseMetadataTypeDef

class SetRepositoryPolicyResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    policyText: str
    ResponseMetadata: ResponseMetadataTypeDef

class StartLifecyclePolicyPreviewResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    lifecyclePolicyText: str
    status: LifecyclePolicyPreviewStatusType
    ResponseMetadata: ResponseMetadataTypeDef

class UpdatePullThroughCacheRuleResponseTypeDef(TypedDict):
    ecrRepositoryPrefix: str
    registryId: str
    updatedAt: datetime
    credentialArn: str
    customRoleArn: str
    upstreamRepositoryPrefix: str
    ResponseMetadata: ResponseMetadataTypeDef

class UploadLayerPartResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    uploadId: str
    lastByteReceived: int
    ResponseMetadata: ResponseMetadataTypeDef

class ValidatePullThroughCacheRuleResponseTypeDef(TypedDict):
    ecrRepositoryPrefix: str
    registryId: str
    upstreamRegistryUrl: str
    credentialArn: str
    customRoleArn: str
    upstreamRepositoryPrefix: str
    isValid: bool
    failure: str
    ResponseMetadata: ResponseMetadataTypeDef

class BatchDeleteImageRequestTypeDef(TypedDict):
    repositoryName: str
    imageIds: Sequence[ImageIdentifierTypeDef]
    registryId: NotRequired[str]

class BatchGetImageRequestTypeDef(TypedDict):
    repositoryName: str
    imageIds: Sequence[ImageIdentifierTypeDef]
    registryId: NotRequired[str]
    acceptedMediaTypes: NotRequired[Sequence[str]]

class DescribeImageReplicationStatusRequestTypeDef(TypedDict):
    repositoryName: str
    imageId: ImageIdentifierTypeDef
    registryId: NotRequired[str]

class DescribeImageScanFindingsRequestTypeDef(TypedDict):
    repositoryName: str
    imageId: ImageIdentifierTypeDef
    registryId: NotRequired[str]
    nextToken: NotRequired[str]
    maxResults: NotRequired[int]

class DescribeImageSigningStatusRequestTypeDef(TypedDict):
    repositoryName: str
    imageId: ImageIdentifierTypeDef
    registryId: NotRequired[str]

class ImageFailureTypeDef(TypedDict):
    imageId: NotRequired[ImageIdentifierTypeDef]
    failureCode: NotRequired[ImageFailureCodeType]
    failureReason: NotRequired[str]

class ImageTypeDef(TypedDict):
    registryId: NotRequired[str]
    repositoryName: NotRequired[str]
    imageId: NotRequired[ImageIdentifierTypeDef]
    imageManifest: NotRequired[str]
    imageManifestMediaType: NotRequired[str]

class ListImagesResponseTypeDef(TypedDict):
    imageIds: list[ImageIdentifierTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class StartImageScanRequestTypeDef(TypedDict):
    repositoryName: str
    imageId: ImageIdentifierTypeDef
    registryId: NotRequired[str]

class UpdateImageStorageClassRequestTypeDef(TypedDict):
    repositoryName: str
    imageId: ImageIdentifierTypeDef
    targetStorageClass: TargetStorageClassType
    registryId: NotRequired[str]

class UpdateImageStorageClassResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    imageId: ImageIdentifierTypeDef
    imageStatus: ImageStatusType
    ResponseMetadata: ResponseMetadataTypeDef

class UploadLayerPartRequestTypeDef(TypedDict):
    repositoryName: str
    uploadId: str
    partFirstByte: int
    partLastByte: int
    layerPartBlob: BlobTypeDef
    registryId: NotRequired[str]

class PutImageTagMutabilityRequestTypeDef(TypedDict):
    repositoryName: str
    imageTagMutability: ImageTagMutabilityType
    registryId: NotRequired[str]
    imageTagMutabilityExclusionFilters: NotRequired[
        Sequence[ImageTagMutabilityExclusionFilterTypeDef]
    ]

class PutImageTagMutabilityResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    imageTagMutability: ImageTagMutabilityType
    imageTagMutabilityExclusionFilters: list[ImageTagMutabilityExclusionFilterTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

class CreateRepositoryCreationTemplateRequestTypeDef(TypedDict):
    prefix: str
    appliedFor: Sequence[RCTAppliedForType]
    description: NotRequired[str]
    encryptionConfiguration: NotRequired[
        EncryptionConfigurationForRepositoryCreationTemplateTypeDef
    ]
    resourceTags: NotRequired[Sequence[TagTypeDef]]
    imageTagMutability: NotRequired[ImageTagMutabilityType]
    imageTagMutabilityExclusionFilters: NotRequired[
        Sequence[ImageTagMutabilityExclusionFilterTypeDef]
    ]
    repositoryPolicy: NotRequired[str]
    lifecyclePolicy: NotRequired[str]
    customRoleArn: NotRequired[str]

class ListTagsForResourceResponseTypeDef(TypedDict):
    tags: list[TagTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

class RepositoryCreationTemplateTypeDef(TypedDict):
    prefix: NotRequired[str]
    description: NotRequired[str]
    encryptionConfiguration: NotRequired[
        EncryptionConfigurationForRepositoryCreationTemplateTypeDef
    ]
    resourceTags: NotRequired[list[TagTypeDef]]
    imageTagMutability: NotRequired[ImageTagMutabilityType]
    imageTagMutabilityExclusionFilters: NotRequired[list[ImageTagMutabilityExclusionFilterTypeDef]]
    repositoryPolicy: NotRequired[str]
    lifecyclePolicy: NotRequired[str]
    appliedFor: NotRequired[list[RCTAppliedForType]]
    customRoleArn: NotRequired[str]
    createdAt: NotRequired[datetime]
    updatedAt: NotRequired[datetime]

class TagResourceRequestTypeDef(TypedDict):
    resourceArn: str
    tags: Sequence[TagTypeDef]

class UpdateRepositoryCreationTemplateRequestTypeDef(TypedDict):
    prefix: str
    description: NotRequired[str]
    encryptionConfiguration: NotRequired[
        EncryptionConfigurationForRepositoryCreationTemplateTypeDef
    ]
    resourceTags: NotRequired[Sequence[TagTypeDef]]
    imageTagMutability: NotRequired[ImageTagMutabilityType]
    imageTagMutabilityExclusionFilters: NotRequired[
        Sequence[ImageTagMutabilityExclusionFilterTypeDef]
    ]
    repositoryPolicy: NotRequired[str]
    lifecyclePolicy: NotRequired[str]
    appliedFor: NotRequired[Sequence[RCTAppliedForType]]
    customRoleArn: NotRequired[str]

class CreateRepositoryRequestTypeDef(TypedDict):
    repositoryName: str
    registryId: NotRequired[str]
    tags: NotRequired[Sequence[TagTypeDef]]
    imageTagMutability: NotRequired[ImageTagMutabilityType]
    imageTagMutabilityExclusionFilters: NotRequired[
        Sequence[ImageTagMutabilityExclusionFilterTypeDef]
    ]
    imageScanningConfiguration: NotRequired[ImageScanningConfigurationTypeDef]
    encryptionConfiguration: NotRequired[EncryptionConfigurationTypeDef]

class PutImageScanningConfigurationRequestTypeDef(TypedDict):
    repositoryName: str
    imageScanningConfiguration: ImageScanningConfigurationTypeDef
    registryId: NotRequired[str]

class PutImageScanningConfigurationResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    imageScanningConfiguration: ImageScanningConfigurationTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class RepositoryTypeDef(TypedDict):
    repositoryArn: NotRequired[str]
    registryId: NotRequired[str]
    repositoryName: NotRequired[str]
    repositoryUri: NotRequired[str]
    createdAt: NotRequired[datetime]
    imageTagMutability: NotRequired[ImageTagMutabilityType]
    imageTagMutabilityExclusionFilters: NotRequired[list[ImageTagMutabilityExclusionFilterTypeDef]]
    imageScanningConfiguration: NotRequired[ImageScanningConfigurationTypeDef]
    encryptionConfiguration: NotRequired[EncryptionConfigurationTypeDef]

class CvssScoreDetailsTypeDef(TypedDict):
    adjustments: NotRequired[list[CvssScoreAdjustmentTypeDef]]
    score: NotRequired[float]
    scoreSource: NotRequired[str]
    scoringVector: NotRequired[str]
    version: NotRequired[str]

class DescribeImageReplicationStatusResponseTypeDef(TypedDict):
    repositoryName: str
    imageId: ImageIdentifierTypeDef
    replicationStatuses: list[ImageReplicationStatusTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

class DescribeImageScanFindingsRequestPaginateTypeDef(TypedDict):
    repositoryName: str
    imageId: ImageIdentifierTypeDef
    registryId: NotRequired[str]
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class DescribePullThroughCacheRulesRequestPaginateTypeDef(TypedDict):
    registryId: NotRequired[str]
    ecrRepositoryPrefixes: NotRequired[Sequence[str]]
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class DescribeRepositoriesRequestPaginateTypeDef(TypedDict):
    registryId: NotRequired[str]
    repositoryNames: NotRequired[Sequence[str]]
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class DescribeRepositoryCreationTemplatesRequestPaginateTypeDef(TypedDict):
    prefixes: NotRequired[Sequence[str]]
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class DescribeImageScanFindingsRequestWaitTypeDef(TypedDict):
    repositoryName: str
    imageId: ImageIdentifierTypeDef
    registryId: NotRequired[str]
    nextToken: NotRequired[str]
    maxResults: NotRequired[int]
    WaiterConfig: NotRequired[WaiterConfigTypeDef]

class StartImageScanResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    imageId: ImageIdentifierTypeDef
    imageScanStatus: ImageScanStatusTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class DescribeImageSigningStatusResponseTypeDef(TypedDict):
    repositoryName: str
    imageId: ImageIdentifierTypeDef
    registryId: str
    signingStatuses: list[ImageSigningStatusTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

DescribeImagesRequestPaginateTypeDef = TypedDict(
    "DescribeImagesRequestPaginateTypeDef",
    {
        "repositoryName": str,
        "registryId": NotRequired[str],
        "imageIds": NotRequired[Sequence[ImageIdentifierTypeDef]],
        "filter": NotRequired[DescribeImagesFilterTypeDef],
        "PaginationConfig": NotRequired[PaginatorConfigTypeDef],
    },
)
DescribeImagesRequestTypeDef = TypedDict(
    "DescribeImagesRequestTypeDef",
    {
        "repositoryName": str,
        "registryId": NotRequired[str],
        "imageIds": NotRequired[Sequence[ImageIdentifierTypeDef]],
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
        "filter": NotRequired[DescribeImagesFilterTypeDef],
    },
)

class DescribePullThroughCacheRulesResponseTypeDef(TypedDict):
    pullThroughCacheRules: list[PullThroughCacheRuleTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

GetLifecyclePolicyPreviewRequestPaginateTypeDef = TypedDict(
    "GetLifecyclePolicyPreviewRequestPaginateTypeDef",
    {
        "repositoryName": str,
        "registryId": NotRequired[str],
        "imageIds": NotRequired[Sequence[ImageIdentifierTypeDef]],
        "filter": NotRequired[LifecyclePolicyPreviewFilterTypeDef],
        "PaginationConfig": NotRequired[PaginatorConfigTypeDef],
    },
)
GetLifecyclePolicyPreviewRequestTypeDef = TypedDict(
    "GetLifecyclePolicyPreviewRequestTypeDef",
    {
        "repositoryName": str,
        "registryId": NotRequired[str],
        "imageIds": NotRequired[Sequence[ImageIdentifierTypeDef]],
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
        "filter": NotRequired[LifecyclePolicyPreviewFilterTypeDef],
    },
)
GetLifecyclePolicyPreviewRequestWaitTypeDef = TypedDict(
    "GetLifecyclePolicyPreviewRequestWaitTypeDef",
    {
        "repositoryName": str,
        "registryId": NotRequired[str],
        "imageIds": NotRequired[Sequence[ImageIdentifierTypeDef]],
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
        "filter": NotRequired[LifecyclePolicyPreviewFilterTypeDef],
        "WaiterConfig": NotRequired[WaiterConfigTypeDef],
    },
)

class ImageDetailTypeDef(TypedDict):
    registryId: NotRequired[str]
    repositoryName: NotRequired[str]
    imageDigest: NotRequired[str]
    imageTags: NotRequired[list[str]]
    imageSizeInBytes: NotRequired[int]
    imagePushedAt: NotRequired[datetime]
    imageScanStatus: NotRequired[ImageScanStatusTypeDef]
    imageScanFindingsSummary: NotRequired[ImageScanFindingsSummaryTypeDef]
    imageManifestMediaType: NotRequired[str]
    artifactMediaType: NotRequired[str]
    lastRecordedPullTime: NotRequired[datetime]
    subjectManifestDigest: NotRequired[str]
    imageStatus: NotRequired[ImageStatusType]
    lastArchivedAt: NotRequired[datetime]
    lastActivatedAt: NotRequired[datetime]

class ListImageReferrersResponseTypeDef(TypedDict):
    referrers: list[ImageReferrerTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class LifecyclePolicyPreviewResultTypeDef(TypedDict):
    imageTags: NotRequired[list[str]]
    imageDigest: NotRequired[str]
    imagePushedAt: NotRequired[datetime]
    action: NotRequired[LifecyclePolicyRuleActionTypeDef]
    appliedRulePriority: NotRequired[int]
    storageClass: NotRequired[LifecyclePolicyStorageClassType]

class LifecyclePolicyPreviewSummaryTypeDef(TypedDict):
    expiringImageTotalCount: NotRequired[int]
    transitioningImageTotalCounts: NotRequired[list[TransitioningImageTotalCountTypeDef]]

ListImageReferrersRequestTypeDef = TypedDict(
    "ListImageReferrersRequestTypeDef",
    {
        "repositoryName": str,
        "subjectId": SubjectIdentifierTypeDef,
        "registryId": NotRequired[str],
        "filter": NotRequired[ListImageReferrersFilterTypeDef],
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)
ListImagesRequestPaginateTypeDef = TypedDict(
    "ListImagesRequestPaginateTypeDef",
    {
        "repositoryName": str,
        "registryId": NotRequired[str],
        "filter": NotRequired[ListImagesFilterTypeDef],
        "PaginationConfig": NotRequired[PaginatorConfigTypeDef],
    },
)
ListImagesRequestTypeDef = TypedDict(
    "ListImagesRequestTypeDef",
    {
        "repositoryName": str,
        "registryId": NotRequired[str],
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
        "filter": NotRequired[ListImagesFilterTypeDef],
    },
)

class PackageVulnerabilityDetailsTypeDef(TypedDict):
    cvss: NotRequired[list[CvssScoreTypeDef]]
    referenceUrls: NotRequired[list[str]]
    relatedVulnerabilities: NotRequired[list[str]]
    source: NotRequired[str]
    sourceUrl: NotRequired[str]
    vendorCreatedAt: NotRequired[datetime]
    vendorSeverity: NotRequired[str]
    vendorUpdatedAt: NotRequired[datetime]
    vulnerabilityId: NotRequired[str]
    vulnerablePackages: NotRequired[list[VulnerablePackageTypeDef]]

class RemediationTypeDef(TypedDict):
    recommendation: NotRequired[RecommendationTypeDef]

class RegistryScanningRuleOutputTypeDef(TypedDict):
    scanFrequency: ScanFrequencyType
    repositoryFilters: list[ScanningRepositoryFilterTypeDef]

class RegistryScanningRuleTypeDef(TypedDict):
    scanFrequency: ScanFrequencyType
    repositoryFilters: Sequence[ScanningRepositoryFilterTypeDef]

class RepositoryScanningConfigurationTypeDef(TypedDict):
    repositoryArn: NotRequired[str]
    repositoryName: NotRequired[str]
    scanOnPush: NotRequired[bool]
    scanFrequency: NotRequired[ScanFrequencyType]
    appliedScanFilters: NotRequired[list[ScanningRepositoryFilterTypeDef]]

class ReplicationRuleOutputTypeDef(TypedDict):
    destinations: list[ReplicationDestinationTypeDef]
    repositoryFilters: NotRequired[list[RepositoryFilterTypeDef]]

class ReplicationRuleTypeDef(TypedDict):
    destinations: Sequence[ReplicationDestinationTypeDef]
    repositoryFilters: NotRequired[Sequence[RepositoryFilterTypeDef]]

class SigningRuleOutputTypeDef(TypedDict):
    signingProfileArn: str
    repositoryFilters: NotRequired[list[SigningRepositoryFilterTypeDef]]

class SigningRuleTypeDef(TypedDict):
    signingProfileArn: str
    repositoryFilters: NotRequired[Sequence[SigningRepositoryFilterTypeDef]]

ResourceTypeDef = TypedDict(
    "ResourceTypeDef",
    {
        "details": NotRequired[ResourceDetailsTypeDef],
        "id": NotRequired[str],
        "tags": NotRequired[dict[str, str]],
        "type": NotRequired[str],
    },
)

class BatchDeleteImageResponseTypeDef(TypedDict):
    imageIds: list[ImageIdentifierTypeDef]
    failures: list[ImageFailureTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

class BatchGetImageResponseTypeDef(TypedDict):
    images: list[ImageTypeDef]
    failures: list[ImageFailureTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

class PutImageResponseTypeDef(TypedDict):
    image: ImageTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class CreateRepositoryCreationTemplateResponseTypeDef(TypedDict):
    registryId: str
    repositoryCreationTemplate: RepositoryCreationTemplateTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class DeleteRepositoryCreationTemplateResponseTypeDef(TypedDict):
    registryId: str
    repositoryCreationTemplate: RepositoryCreationTemplateTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class DescribeRepositoryCreationTemplatesResponseTypeDef(TypedDict):
    registryId: str
    repositoryCreationTemplates: list[RepositoryCreationTemplateTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class UpdateRepositoryCreationTemplateResponseTypeDef(TypedDict):
    registryId: str
    repositoryCreationTemplate: RepositoryCreationTemplateTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class CreateRepositoryResponseTypeDef(TypedDict):
    repository: RepositoryTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class DeleteRepositoryResponseTypeDef(TypedDict):
    repository: RepositoryTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class DescribeRepositoriesResponseTypeDef(TypedDict):
    repositories: list[RepositoryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class ScoreDetailsTypeDef(TypedDict):
    cvss: NotRequired[CvssScoreDetailsTypeDef]

class DescribeImagesResponseTypeDef(TypedDict):
    imageDetails: list[ImageDetailTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class GetLifecyclePolicyPreviewResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    lifecyclePolicyText: str
    status: LifecyclePolicyPreviewStatusType
    previewResults: list[LifecyclePolicyPreviewResultTypeDef]
    summary: LifecyclePolicyPreviewSummaryTypeDef
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class RegistryScanningConfigurationTypeDef(TypedDict):
    scanType: NotRequired[ScanTypeType]
    rules: NotRequired[list[RegistryScanningRuleOutputTypeDef]]

RegistryScanningRuleUnionTypeDef = Union[
    RegistryScanningRuleTypeDef, RegistryScanningRuleOutputTypeDef
]

class BatchGetRepositoryScanningConfigurationResponseTypeDef(TypedDict):
    scanningConfigurations: list[RepositoryScanningConfigurationTypeDef]
    failures: list[RepositoryScanningConfigurationFailureTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

class ReplicationConfigurationOutputTypeDef(TypedDict):
    rules: list[ReplicationRuleOutputTypeDef]

class ReplicationConfigurationTypeDef(TypedDict):
    rules: Sequence[ReplicationRuleTypeDef]

class SigningConfigurationOutputTypeDef(TypedDict):
    rules: list[SigningRuleOutputTypeDef]

class SigningConfigurationTypeDef(TypedDict):
    rules: Sequence[SigningRuleTypeDef]

EnhancedImageScanFindingTypeDef = TypedDict(
    "EnhancedImageScanFindingTypeDef",
    {
        "awsAccountId": NotRequired[str],
        "description": NotRequired[str],
        "findingArn": NotRequired[str],
        "firstObservedAt": NotRequired[datetime],
        "lastObservedAt": NotRequired[datetime],
        "packageVulnerabilityDetails": NotRequired[PackageVulnerabilityDetailsTypeDef],
        "remediation": NotRequired[RemediationTypeDef],
        "resources": NotRequired[list[ResourceTypeDef]],
        "score": NotRequired[float],
        "scoreDetails": NotRequired[ScoreDetailsTypeDef],
        "severity": NotRequired[str],
        "status": NotRequired[str],
        "title": NotRequired[str],
        "type": NotRequired[str],
        "updatedAt": NotRequired[datetime],
        "fixAvailable": NotRequired[str],
        "exploitAvailable": NotRequired[str],
    },
)

class GetRegistryScanningConfigurationResponseTypeDef(TypedDict):
    registryId: str
    scanningConfiguration: RegistryScanningConfigurationTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class PutRegistryScanningConfigurationResponseTypeDef(TypedDict):
    registryScanningConfiguration: RegistryScanningConfigurationTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class PutRegistryScanningConfigurationRequestTypeDef(TypedDict):
    scanType: NotRequired[ScanTypeType]
    rules: NotRequired[Sequence[RegistryScanningRuleUnionTypeDef]]

class DescribeRegistryResponseTypeDef(TypedDict):
    registryId: str
    replicationConfiguration: ReplicationConfigurationOutputTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class PutReplicationConfigurationResponseTypeDef(TypedDict):
    replicationConfiguration: ReplicationConfigurationOutputTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

ReplicationConfigurationUnionTypeDef = Union[
    ReplicationConfigurationTypeDef, ReplicationConfigurationOutputTypeDef
]

class DeleteSigningConfigurationResponseTypeDef(TypedDict):
    registryId: str
    signingConfiguration: SigningConfigurationOutputTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class GetSigningConfigurationResponseTypeDef(TypedDict):
    registryId: str
    signingConfiguration: SigningConfigurationOutputTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class PutSigningConfigurationResponseTypeDef(TypedDict):
    signingConfiguration: SigningConfigurationOutputTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

SigningConfigurationUnionTypeDef = Union[
    SigningConfigurationTypeDef, SigningConfigurationOutputTypeDef
]

class ImageScanFindingsTypeDef(TypedDict):
    imageScanCompletedAt: NotRequired[datetime]
    vulnerabilitySourceUpdatedAt: NotRequired[datetime]
    findingSeverityCounts: NotRequired[dict[FindingSeverityType, int]]
    findings: NotRequired[list[ImageScanFindingTypeDef]]
    enhancedFindings: NotRequired[list[EnhancedImageScanFindingTypeDef]]

class PutReplicationConfigurationRequestTypeDef(TypedDict):
    replicationConfiguration: ReplicationConfigurationUnionTypeDef

class PutSigningConfigurationRequestTypeDef(TypedDict):
    signingConfiguration: SigningConfigurationUnionTypeDef

class DescribeImageScanFindingsResponseTypeDef(TypedDict):
    registryId: str
    repositoryName: str
    imageId: ImageIdentifierTypeDef
    imageScanStatus: ImageScanStatusTypeDef
    imageScanFindings: ImageScanFindingsTypeDef
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]
