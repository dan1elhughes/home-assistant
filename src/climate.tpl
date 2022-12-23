{% for room in rooms %}
{% if room.heaterPrefix %}
- platform: generic_thermostat
  unique_id: thermostat_{{room.name | lower | replace(" ", "_")}}
  name: {{room.name}}
  initial_hvac_mode: "heat"
  heater: {{room.heaterPrefix}}power
  target_sensor: {{room.sensorPrefix}}temperature
  away_temp: 12
  sleep_temp: 15
  home_temp: 18
  comfort_temp: 19
  max_temp: 25
{% endif %}
{% endfor %}
