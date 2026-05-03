extends ColorRect

var status_path := OS.get_environment("HOME") + "/cyberdeck/wall_status.json"
var target_intensity := 0.0
var target_pulse := 0.0
var current_intensity := 0.0
var current_pulse := 0.0

func _ready():
    # Fullscreen, no decoration
    anchors_preset = PRESET_FULL_RECT
    # Read status on a timer
    var timer = Timer.new()
    timer.wait_time = 2.0
    timer.autostart = true
    timer.timeout.connect(_read_status)
    add_child(timer)
    _read_status()

func _read_status():
    var file = FileAccess.open(status_path, FileAccess.READ)
    if file == null:
        target_intensity = 0.0
        target_pulse = 0.0
        return
    var text = file.get_as_text()
    file.close()
    var data = JSON.parse_string(text)
    if data == null:
        return
    var state = data.get("state", "IDLE")
    match state:
        "IDLE":
            target_intensity = 0.0
            target_pulse = 0.0
        "BLOCKED":
            target_intensity = 0.3
            target_pulse = 0.5
        "WATCHING":
            target_intensity = 0.6
            target_pulse = 0.3
        "STORM":
            target_intensity = 1.0
            target_pulse = 1.0

func _process(delta):
    # Smooth transitions between states
    current_intensity = lerp(current_intensity, target_intensity, delta * 2.0)
    current_pulse = lerp(current_pulse, target_pulse, delta * 3.0)
    material.set_shader_parameter("intensity", current_intensity)
    material.set_shader_parameter("pulse", current_pulse)
