{% for room in rooms %}
{% if room.heater and room.temperature %}
- platform: generic_thermostat
  unique_id: "thermostat_{{room.id}}"
  name: "{{room.name}}"
  initial_hvac_mode: "off"
  heater: "{{room.heater}}"
  target_sensor: "{{room.temperature}}"
  away_temp: 12
  sleep_temp: 15
  home_temp: 17
  comfort_temp: 18
  min_temp: 10
  max_temp: 25
  cold_tolerance: 0.2
  hot_tolerance: 0.2
  precision: 0.5
{% endif %}
{% endfor %}
