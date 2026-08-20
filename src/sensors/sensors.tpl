- platform: filter
  name: "Filtered UCG Max temperature"
  entity_id: sensor.ucg_max_ucg_max_cpu_temperature
  filters:
    - filter: time_throttle
      window_size: "00:01"

- platform: derivative
  source: sensor.barn_ac_energy
  name: Current Barn AC Power Draw
  round: 2
  unit_time: h
  time_window: "00:30:00"

{% for q in immich_queues %}
- platform: derivative
  source: sensor.immich_{{ q.name | lower | replace(' ', '_') }}_queued
  name: Immich {{ q.name }} Rate per Hour
  unique_id: immich_{{ q.name | lower | replace(' ', '_') }}_rate_per_hour
  round: 1
  unit_time: h
  time_window: "00:05:00"
{% endfor %}
