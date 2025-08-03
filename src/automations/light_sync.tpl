{% for sync in light_sync %}
- alias: "Light sync from {{ sync.source }}"
  mode: queued
  trigger:
    - platform: state
      entity_id: {{ sync.source }}
  action:
    - choose:
        - conditions:
            - condition: state
              entity_id: {{ sync.source }}
              state: "on"
          sequence:
            {% for target in sync.targets %}
            - service: light.turn_on
              target:
                entity_id:
                  - {{ target }}
            {% endfor %}
        - conditions:
            - condition: state
              entity_id: {{ sync.source }}
              state: "off"
          sequence:
            {% for target in sync.targets %}
            - service: light.turn_off
              target:
                entity_id:
                  - {{ target }}
            {% endfor %}
{% endfor %}
