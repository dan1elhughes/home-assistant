{% for button in buttons %}
### {{ button.name }} ###
- alias: "{{ button.name }}"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: {{ button.ieee }}
  action:
    - choose:
        {% for command, scene in button.actions %}
        - conditions: "{% raw %}{{{% endraw %} trigger.event.data.command == '{{ command }}' {% raw %}}}{% endraw %}"
          alias: "{{ command }} -> {{ scene }}"
          sequence:
            - scene: {{ scene }}

        {% if command == 'on' %}
        - conditions: "{% raw %}{{ trigger.event.data.command == 'off_with_effect' }}{% endraw %}"
          alias: "off_with_effect -> {{ scene }}"
          sequence:
            - scene: {{ scene }}
        {% endif %}
        {% endfor %}
{% endfor %}
