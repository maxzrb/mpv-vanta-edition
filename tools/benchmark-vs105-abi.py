"""MIT License

Copyright (c) 2026 user-Wing

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
# ABI 定义来自 user-Wing/VS-Renderer-GUI（MIT），提交 420dd3ee53a918a244c0c332f352714e29a6c9a4。
# 对应 src/backend/ThreeFpApi.h；测试 DLL 必须核对 API 版本，不能通用于所有 3FP 分支。
import ctypes as C
class ThreeFpConfiguration(C.Structure):
    _fields_ = [
        ('size', C.c_uint32),
        ('version', C.c_uint32),
        ('outputWindow', C.c_void_p),
        ('decodeMode', C.c_uint32),
        ('colorMode', C.c_uint32),
        ('sdrPeakNits', C.c_float),
        ('hdrPeakNits', C.c_float),
        ('sdrPaperWhiteNits', C.c_float),
        ('audioEndpointIdUtf8', C.c_char_p),
        ('eventCallback', C.c_void_p),
        ('eventCallbackContext', C.c_void_p),
        ('videoScalingQuality', C.c_uint32),
        ('forceHdrOutput', C.c_uint32),
        ('preferredAdapterIndex', C.c_int32),
        ('sdrScRgbMode', C.c_uint32)
    ]

class ThreeFpSnapshot(C.Structure):
    _fields_ = [
        ('size', C.c_uint32),
        ('version', C.c_uint32),
        ('state', C.c_uint32),
        ('decodeMode', C.c_uint32),
        ('requestedColorMode', C.c_uint32),
        ('actualColorMode', C.c_uint32),
        ('position100ns', C.c_int64),
        ('duration100ns', C.c_int64),
        ('frameIndex', C.c_int64),
        ('framePts', C.c_int64),
        ('frameTimeBaseNumerator', C.c_int32),
        ('frameTimeBaseDenominator', C.c_int32),
        ('selectedVideoStream', C.c_int32),
        ('selectedAudioStream', C.c_int32),
        ('videoWidth', C.c_uint32),
        ('videoHeight', C.c_uint32),
        ('isHdrSource', C.c_uint32),
        ('isExternalAudio', C.c_uint32),
        ('externalAudioOffset100ns', C.c_int64),
        ('decodedVideoFrames', C.c_uint64),
        ('presentedVideoFrames', C.c_uint64),
        ('droppedVideoFrames', C.c_uint64),
        ('queuedVideoFrames', C.c_uint32),
        ('sourcePeakNits', C.c_uint32),
        ('decodedAudioFrames', C.c_uint64),
        ('audioPosition100ns', C.c_int64),
        ('bufferedAudio100ns', C.c_int64),
        ('audioUnderruns', C.c_uint64),
        ('audioTimestampJitterFrames', C.c_uint64),
        ('audioDiscontinuities', C.c_uint64),
        ('audioInsertedSilenceFrames', C.c_uint64),
        ('audioDroppedOverlapFrames', C.c_uint64),
        ('coalescedVideoFrames', C.c_uint64),
        ('audioRejectedFrames', C.c_uint64),
        ('swapChainPresents', C.c_uint64),
        ('presentWait100ns', C.c_uint64),
        ('deviceLockWait100ns', C.c_uint64),
        ('hardwareTransfer100ns', C.c_uint64),
        ('softwareConvert100ns', C.c_uint64),
        ('videoBitRate', C.c_uint64),
        ('audioBitRate', C.c_uint64),
        ('videoOutputBitDepth', C.c_uint32),
        ('videoScalingMode', C.c_uint32),
        ('timelineGeneration', C.c_uint64),
        ('hdrFormat', C.c_uint32),
        ('compatibleHdrFormats', C.c_uint32),
        ('hdrProcessingPath', C.c_uint32),
        ('dolbyVisionProfile', C.c_uint32),
        ('dolbyVisionLevel', C.c_uint32),
        ('hasDolbyVisionRpu', C.c_uint32),
        ('hasDolbyVisionEnhancementLayer', C.c_uint32),
        ('dolbyVisionEnhancementLayer', C.c_uint32),
        ('dynamicHdrMetadataActive', C.c_uint32),
        ('hdrFallbackActive', C.c_uint32),
        ('displayMinLuminanceMilliNits', C.c_uint32),
        ('displayPeakNits', C.c_uint32),
        ('displayFullFramePeakNits', C.c_uint32),
        ('effectiveTargetPeakNits', C.c_uint32)
    ]
