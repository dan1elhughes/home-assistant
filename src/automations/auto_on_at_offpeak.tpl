### Auto on at offpeak ###
- alias: "Auto on at offpeak"
  mode: single
  trigger:
    - platform: state
      entity_id: binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak
      to: "on"
  action:
    - service: homeassistant.turn_on
      target:
        entity_id:
{% for e in autoOnAtOffpeak %}
          - {{ e }}
{% endfor %}
