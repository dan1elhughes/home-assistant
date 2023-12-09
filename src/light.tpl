{% for id, group in groups %}
# {{ id }}
- platform: group
  name: {{ group.name }}
  entities:
    {% for entity in group.entities %}
    - {{ entity }}
    {% endfor %}
{% endfor %}
