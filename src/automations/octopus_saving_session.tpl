{% import '../macros/lights.tpl' as lights with context %}

- alias: "Saving session: started"
  mode: single
  trigger:
    - platform: state
      entity_id: binary_sensor.octopus_energy_a_fad3b08a_octoplus_saving_sessions
      from: "off"
      to: "on"
  condition:
    - condition: state
      entity_id: input_boolean.automations
      state: "on"
  action:
    - service: notify.dan
      data:
        title: ⚡ Saving session ⚡
        message: Heating disabled
        data:
          channel: "Heating"
          notification_icon: "mdi:heat-wave"
    - service: climate.set_hvac_mode
      target:
        entity_id: group.thermostats
      data:
        hvac_mode: "off"
    - service: switch.turn_off
      target:
        entity_id: switch.sinkhole
    - service: light.turn_off
      target:
        entity_id:
          {{- lights.ids() | indent(10) }}

- alias: "Saving session: ended while home"
  mode: single
  trigger:
    - platform: state
      entity_id: binary_sensor.octopus_energy_a_fad3b08a_octoplus_saving_sessions
      from: "on"
      to: "off"
  condition:
    - condition: state
      entity_id: group.presence_home
      state: home
    - condition: state
      entity_id: input_boolean.automations
      state: "on"
  action:
    - service: notify.dan
      data:
        title: ⚡ Saving session ⚡
        message: Heating re-enabled
        data:
          channel: "Heating"
          notification_icon: "mdi:heat-wave"
    - service: climate.set_hvac_mode
      target:
        entity_id: group.thermostats
      data:
        hvac_mode: "heat"
    - service: switch.turn_on
      target:
        entity_id: switch.sinkhole
