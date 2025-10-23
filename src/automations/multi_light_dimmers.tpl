{% for x in multiLightDimmers %}
- alias: {{x.name}}
  use_blueprint:
    path: candeosmart/candeo-blueprint-sr5br-ZHA-multi-light-control.yaml
    input:
      selected_light_helper: input_select.{{ x.id }}
      sr5br_device: {{ x.sr5br_device }}
      light_1: {{ x.light_1 }}
      light_2: {{ x.light_2 }}
      light_3: {{ x.light_3 }}
      light_4: {{ x.light_4 }}

- alias: "{{ x.name }} hold"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_id: "{{ x.sr5br_device }}"
        command: "centre_button_hold"
  action:
    - service: light.turn_off
      target:
        entity_id: "{{ x.light_group }}"

- alias: "{{ x.name }} select"
  mode: single
  trigger:
    - platform: state
      entity_id: input_select.{{ x.id }}
  action:
    - choose:
        - conditions: >
            {% raw %}{{ trigger.to_state.state == '1' }}{% endraw %}
          sequence:
            - service: light.turn_on
              target:
                entity_id: "{{ x.light_1 }}"
              data:
                brightness_pct: 1
        - conditions: >
            {% raw %}{{ trigger.to_state.state == '2' }}{% endraw %}
          sequence:
            - service: light.turn_on
              target:
                entity_id: "{{ x.light_2 }}"
              data:
                brightness_pct: 1
        - conditions: >
            {% raw %}{{ trigger.to_state.state == '3' }}{% endraw %}
          sequence:
            - service: light.turn_on
              target:
                entity_id: "{{ x.light_3 }}"
              data:
                brightness_pct: 1
        - conditions: >
            {% raw %}{{ trigger.to_state.state == '4' }}{% endraw %}
          sequence:
            - service: light.turn_on
              target:
                entity_id: "{{ x.light_4 }}"
              data:
                brightness_pct: 1
{% endfor %}
