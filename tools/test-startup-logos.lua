-- 徽标识别以当前真实格式为准，文件名或无关轨道标题不升级格式。
local info = dofile('portable_config/script-modules/media-format-info.lua')
assert(info.from_snapshot({audio_codec='dra',audio_track={type='audio',codec='dra'}}).audio_codec == 'DRA')
assert(info.from_snapshot({audio_codec='aac',audio_track={type='audio',codec='aac',title='DRA Atmos DTS:X'}}).audio_codec == 'AAC')
assert(info.from_snapshot({video_codec='hevc',video_track={type='video',title='HDR Dolby Vision'},
    video_params={w=640,h=360,gamma='bt.1886',primaries='bt.709'}}).dynamic_range == 'SDR')
assert(info.from_snapshot({video_codec='hevc',video_params={w=640,h=360,gamma='pq',primaries='bt.2020'}}).dynamic_range == 'HDR')
assert(info.from_snapshot({video_codec='hevc',video_params={w=640,h=360,gamma='hlg',primaries='bt.2020'}}).dynamic_range == 'HLG')
print('PASS DRA／真实音频优先／SDR、PQ、HLG 徽标识别')
