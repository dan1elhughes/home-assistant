{% macro lights(entry) -%}
### {{ entry.name }} ###
- alias: "{{ entry.name }} automatic lights on"
  mode: single
  trigger:
    {%- for sensor in entry.triggers %}
    - platform: state
      entity_id: {{ sensor }}
      to: "on"
    {%- endfor %}
  {%- if entry.night_only %}
  condition:
    - condition: state
      entity_id: sun.sun
      state: "below_horizon"
  {%- endif %}
  action:
    {%- if entry.day_brightness and entry.night_brightness and entry.day_brightness != entry.night_brightness %}
    - choose:
        - conditions:
            - condition: state
              entity_id: sun.sun
              state: "above_horizon"
          sequence:
            - action: light.turn_on
              target:
                entity_id: {{ entry.light }}
              data:
                brightness_pct: {{ entry.day_brightness }}
        - conditions:
            - condition: state
              entity_id: sun.sun
              state: "below_horizon"
          sequence:
            - action: light.turn_on
              target:
                entity_id: {{ entry.light }}
              data:
                brightness_pct: {{ entry.night_brightness }}
    {%- elif entry.day_brightness %}
    - action: light.turn_on
      target:
        entity_id: {{ entry.light }}
      data:
        brightness_pct: {{ entry.day_brightness }}
    {%- else %}
    - action: light.turn_on
      target:
        entity_id: {{ entry.light }}
    {%- endif %}

- alias: "{{ entry.name }} automatic lights off"
  mode: single
  trigger:
    {%- for sensor in entry.triggers %}
    - platform: state
      entity_id: {{ sensor }}
      to: "off"
      for:
        minutes: 5
    {%- endfor %}
  condition:
    {%- for sensor in entry.triggers %}
    - condition: state
      entity_id: {{ sensor }}
      state: "off"
    {%- endfor %}
    {%- if entry.night_only %}
    - condition: state
      entity_id: sun.sun
      state: "below_horizon"
    {%- endif %}
  action:
    - action: light.turn_off
      target:
        entity_id: {{ entry.light }}
{%- if entry.sunset %}

- alias: "{{ entry.name }} automatic lights on at sunset"
  mode: single
  trigger:
    - platform: sun
      event: sunset
  action:
    - action: light.turn_on
      target:
        entity_id: {{ entry.light }}
{%- endif %}
{%- if entry.off_at %}

- alias: "{{ entry.name }} automatic lights off at {{ entry.off_at }}"
  mode: single
  trigger:
    - platform: time
      at: "{{ entry.off_at }}"
  {%- if entry.night_only %}
  condition:
    - condition: state
      entity_id: sun.sun
      state: "below_horizon"
  {%- endif %}
  action:
    - action: light.turn_off
      target:
        entity_id: {{ entry.light }}
{%- endif %}
{% endmacro -%}

{% for entry in automatic_lights -%}
{{ lights(entry) }}
{% endfor %}
