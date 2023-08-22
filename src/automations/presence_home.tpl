- alias: "Leave home (active room -> out)"
  mode: single
  trigger:
    - platform: state
      entity_id: group.presence_home
      from: home
      to: not_home
  condition:
    - condition: state
      entity_id: input_boolean.lighting_automations
      state: "on"
  action:
    - service: input_select.select_option
      target:
        entity_id: input_select.active_room
      data:
        option: "out"

- alias: "Arrive home (active room -> bedroom)"
  mode: single
  trigger:
    - platform: state
      entity_id: group.presence_home
      from: not_home
      to: home
  condition:
    - condition: state
      entity_id: input_boolean.lighting_automations
      state: "on"
  action:
    - service: input_select.select_option
      target:
        entity_id: input_select.active_room
      data:
        option: "bedroom"

- alias: "Presence monitoring"
  mode: single
  trigger:
    - platform: state
      entity_id:
        {%- for person in people %}
        - {{ person }}
        {%- endfor %}
      to: null
  condition:
    - condition: state
      entity_id: input_boolean.presence_notifications
      state: "on"
  action:
    - service: notify.dan
      data:
        message: "{% raw %}{{ trigger.entity_id }} is now {{ trigger.to_state.state }}{% endraw %}"
        data:
          channel: "Presence"
          tag: presence
          notification_icon: "mdi:account-multiple"
