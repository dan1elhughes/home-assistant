### Bedroom buttons ###
- alias: "Bedroom buttons"
  mode: single
  trigger:
    {% for button in buttons %}
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: {{ button.ieee }}
    {% endfor %}
  action:
    - choose:
        {% for button in buttons %}
        - conditions: "{% raw %}{{{% endraw %} trigger.event.data.device_ieee == '{{ button.ieee }}' and trigger.event.data.command == 'on_press' {% raw %}}}{% endraw %}"
          alias: "{{ button.name }} single press"
          sequence:
            - action: light.turn_on
              entity_id: {{ button.light }}
              data:
                brightness_pct: 1

        - conditions: "{% raw %}{{{% endraw %} trigger.event.data.device_ieee == '{{ button.ieee }}' and trigger.event.data.command == 'on_hold' {% raw %}}}{% endraw %}"
          alias: "{{ button.name }} long press"
          sequence:
            - action: light.turn_off
              entity_id: {{ button.light }}

        - conditions: "{% raw %}{{{% endraw %} trigger.event.data.device_ieee == '{{ button.ieee }}' and trigger.event.data.command == 'on_double_press' {% raw %}}}{% endraw %}"
          alias: "{{ button.name }} double press"
          sequence:
            - action: light.turn_off
              entity_id: {{ button.double_off }}
        {% endfor %}
