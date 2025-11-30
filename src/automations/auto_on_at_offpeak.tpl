### Auto on/off at offpeak ###
- alias: "Auto on/off at offpeak"
  mode: single
  trigger:
    - platform: state
      entity_id: binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak
  action:
    choose:
      - conditions:
          - condition: state
            entity_id: binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak
            state: "on"
        sequence:
          - service: homeassistant.turn_on
            target:
              entity_id:
                - switch.off_peak
      - conditions:
          - condition: state
            entity_id: binary_sensor.octopus_energy_electricity_15p0706167_2000050773706_off_peak
            state: "off"
        sequence:
          - service: homeassistant.turn_off
            target:
              entity_id:
                - switch.off_peak
