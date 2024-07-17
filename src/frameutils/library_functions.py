#Injecting this as lua code is a hack, it ideally would be handled on the frame itself internal to the built-in print() function
library_print_long = """
function prntLng(stringToPrint)
	local mtu = frame.bluetooth.max_length()
	local len = string.len(stringToPrint)
	if len <= mtu - 3 then
		print(stringToPrint)
		return
	end
	local i = 1
	local chunkIndex = 0
	while i <= len do
		local j = i + mtu - 4
		if j > len then
			j = len
		end
		local chunk = string.sub(stringToPrint, i, j)
		print("\\010"..chunk)
		chunkIndex = chunkIndex + 1
		i = j + 1
	end
	print("\\011"..chunkIndex)
end
function sendPartial(dataToSend, max_size)
	local len = string.len(dataToSend)
	local i = 1
	local chunkIndex = 0
	while i <= len do
		local j = i + max_size - 4
		if j > len then
			j = len
		end
		local chunk = string.sub(dataToSend, i, j)
		while true do
			if pcall(frame.bluetooth.send, '\\001' .. chunk) then
				break
			end
		end
		chunkIndex = chunkIndex + 1
		i = j + 1
	end
	return chunkIndex
end
function printCompleteFile(filename)
	local mtu = frame.bluetooth.max_length()
	local f = frame.file.open(filename, "read")
	local chunkIndex = 0
	local chunk = ""
	while true do
		local new_chunk = f:read()
		if new_chunk == nil then
			if string.len(chunk) > 0 then
				chunkIndex = chunkIndex + sendPartial(chunk, mtu)
				break
			end
			break
		end
		if string.len(new_chunk) == 512 then
			chunk = chunk .. new_chunk
		else
			chunk = chunk .. new_chunk .. "\\n"
		end
		
		while string.len(chunk) > mtu - 4 do
			local chunk_to_send = string.sub(chunk, 1, mtu - 4)
			chunkIndex = chunkIndex + 1
			chunk = string.sub(chunk, mtu - 3)
			while true do
				if pcall(frame.bluetooth.send, '\\001' .. chunk_to_send) then
					break
				end
			end
		end
	end
	while true do
		if pcall(frame.bluetooth.send, '\\002' .. chunkIndex) then
			break
		end
	end
	f:close()
end
function cameraCaptureAndSend(quality,autoExpTimeDelay,autofocusType)
	local last_autoexp_time = 0
    local state = 'EXPOSING'
    local state_time = frame.time.utc()
    local chunkIndex = 0
    if autoExpTimeDelay == nil then
        state = 'CAPTURE'
    end

    while true do
        if state == 'EXPOSING' then
            if frame.time.utc() - last_autoexp_time > 0.1 then
                frame.camera.auto { metering = autofocusType }
                last_autoexp_time = frame.time.utc()
            end
            if frame.time.utc() > state_time + autoExpTimeDelay then
                state = 'CAPTURE'
            end
        elseif state == 'CAPTURE' then
            frame.camera.capture { quality_factor = quality }
            state_time = frame.time.utc()
            state = 'WAIT'
        elseif state == 'WAIT' then
            if frame.time.utc() > state_time + 0.5 then
                state = 'SEND'
            end
        elseif state == 'SEND' then
            local i = frame.camera.read(frame.bluetooth.max_length() - 1)
            if (i == nil) then
                state = 'DONE'
            else
                while true do
                    if pcall(frame.bluetooth.send, '\\001' .. i) then
                        break
                    end
                end
                chunkIndex = chunkIndex + 1
            end
        elseif state == 'DONE' then
            while true do
                if pcall(frame.bluetooth.send, '\\002' .. chunkIndex) then
                    break
                end
            end
            break
        end
    end
end
"""