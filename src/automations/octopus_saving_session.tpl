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
        message: started
        data:
          channel: "saving-session"
          notification_icon: "mdi:heat-wave"
    - service: homeassistant.turn_off
      target:
        entity_id:
          {% for id in savingSessionDevices %}
          - {{ id }}
          {% endfor %}

    - scene: scene.lights_off

- alias: "Saving session: ended while home"
  mode: single
  trigger:
    - platform: state
      entity_id: binary_sensor.octopus_energy_a_fad3b08a_octoplus_saving_sessions
      from: "on"
      to: "off"
  condition:
    - condition: state
      entity_id: input_boolean.automations
      state: "on"
  action:
    - service: notify.dan
      data:
        title: ⚡ Saving session ⚡
        message: Ended
        data:
          channel: "saving-session"
          notification_icon: "mdi:heat-wave"
    - service: homeassistant.turn_on
      target:
        entity_id:
          {% for id in savingSessionDevices %}
          - {{ id }}
          {% endfor %}
