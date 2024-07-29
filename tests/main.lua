while true do
    frame.display.text('Hello world!', 10, 10)
    frame.display.show()
    frame.sleep(1)

    frame.display.text('Test was run from file', 10, 10, { color = 'RED' })
    frame.display.show()
    frame.sleep(1)
end
