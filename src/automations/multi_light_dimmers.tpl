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
{% endfor %}
