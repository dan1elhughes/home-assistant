- alias: "Leave home (active room -> out)"
  mode: single
  trigger:
    - platform: state
      entity_id: group.presence_home
      from: home
      to: not_home
  condition:
    - condition: state
      entity_id: input_boolean.automations
      state: "on"

    - not:
      {% for person in people %}
      - condition: state
        entity_id: {{ person }}
        state: "unknown"
      {% endfor %}
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
      entity_id: input_boolean.automations
      state: "on"
  # Only run if we've not outpaced the automation and already set the active room
    - condition: state
      entity_id: input_select.active_room
      state: "out"

    - not:
      {% for person in people %}
      - condition: state
        entity_id: {{ person }}
        state: "unknown"
      {% endfor %}
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
        {%- for person in people -%}
        {%- if person != "person.dan" %}
        - {{ person }}
        {%- endif -%}
        {%- endfor %}
      to: null
  action:
    - service: notify.dan
      data:
        message: "{% raw %}{{ trigger.entity_id  | replace('person.', '') | title }} is now {{ trigger.to_state.state }}{% endraw %}"
        data:
          channel: "Presence"
          tag: presence
          notification_icon: "mdi:account-multiple"
