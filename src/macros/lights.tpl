{% macro ids() %}
{% for room in rooms -%}
{% if room.lights -%}
# {{ groups[room.lights].name }}
{% for id in groups[room.lights].entities -%}
- {{ id }}
{% endfor -%}
{% endif -%}
{% endfor %}
{% endmacro %}
