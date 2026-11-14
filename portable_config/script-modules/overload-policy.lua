-- 过载追赶的时间判定；输入播放快照，输出请求，不直接操作播放器。
-- License: MIT
local M = {}

function M.new(o)
    local self = {o = o, high_since = nil, low_since = nil, not_before = 0,
        changed_at = 0, retry_at = 0, retries = 0, probe_at = nil,
        sync_at = 0, sync_retries = 0}

    function self:interrupt(now)
        self.high_since, self.low_since = nil, nil
        self.sync_since, self.drop_sample, self.drop_pressure = nil, nil, false
        self.drop_seen, self.drop_at = nil, nil
        self.not_before = now + self.o.settle
    end

    function self:reset(now)
        self.changed_at, self.retry_at, self.retries, self.probe_at = now, 0, 0, nil
        self.sync_at, self.sync_retries = now, 0
        self:interrupt(now)
    end

    function self:commit(reference, now)
        if reference then
            if self.probe_at and now - self.probe_at < self.o.retry then
                self.retries = math.min(self.retries + 1, 3)
            end
            self.retry_at = now + math.min(self.o.retry * 2 ^ self.retries, 240)
            self.probe_at = nil
        else
            self.probe_at = now
        end
        self.changed_at = now
        self.sync_at, self.sync_retries = now + (self.o.sync_interval or 10), 0
        self:interrupt(now)
    end

    function self:resynced(now)
        self.sync_retries = math.min(self.sync_retries + 1, 4)
        self.sync_at = now + math.min((self.o.sync_interval or 10) * 2 ^ (self.sync_retries - 1), 60)
        self:interrupt(now)
    end

    function self:dropping(s)
        local count, fps, speed = tonumber(s.dropped), tonumber(s.fps), tonumber(s.speed) or 1
        if not count or not fps or fps <= 0 or speed <= 0 then return false end
        if self.drop_seen and count > self.drop_seen then self.drop_at = s.now
        elseif self.drop_seen and count < self.drop_seen then self.drop_at = nil end
        self.drop_seen = count
        local previous = self.drop_sample
        if not previous or count < previous.count or speed ~= previous.speed then
            self.drop_sample = {now = s.now, count = count, speed = speed}
            self.drop_pressure = false
        elseif s.now - previous.now >= (self.o.drop_window or 2) then
            local delta = count - previous.count
            self.drop_pressure = delta >= 3 and delta / (fps * speed * (s.now - previous.now))
                >= (self.o.drop_ratio or .05)
            self.drop_sample = {now = s.now, count = count, speed = speed}
        end
        -- 窗口统计不能让已经停止的瞬间掉帧继续积累“持续过载”时间。
        return self.drop_pressure and self.drop_at
            and s.now - self.drop_at <= (self.o.drop_window or 2) / 2 or false
    end

    function self:step(s)
        if s.blocked then self:interrupt(s.now); return end
        if s.busy or s.now < self.not_before then return end
        local lag = tonumber(s.lag)
        if not lag or lag ~= lag or lag == math.huge or lag == -math.huge then
            self:interrupt(s.now)
            return
        end
        if s.reference then
            self.high_since = nil
            -- 已省略画面的低延迟不能证明完整解码有余量；默认本片保持，不自动探测。
            if lag >= (self.o.sync_lag or .75) then
                self.sync_since = self.sync_since or s.now
                if s.now >= self.sync_at and s.now - self.sync_since >= (self.o.sync_hold or 2) then
                    return 'resync'
                end
            else
                self.sync_since = nil
            end
            if self.o.recover and math.abs(lag) <= self.o.leave_lag then
                self.low_since = self.low_since or s.now
                if s.now >= self.retry_at and s.now - self.low_since >= self.o.leave_hold
                    and s.now - self.changed_at >= self.o.minimum then return 'full' end
            else
                self.low_since = nil
            end
        else
            self.low_since = nil
            local dropping = self:dropping(s)
            if lag >= self.o.enter_lag or dropping then
                self.high_since = self.high_since or s.now
                if s.now - self.high_since >= self.o.enter_hold then return 'reference' end
            else
                self.high_since = nil
            end
        end
    end

    return self
end

return M
