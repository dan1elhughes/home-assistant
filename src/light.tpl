{% for id, group in groups %}
# {{ id }}
- platform: group
  name: {{ group.name }}
  unique_id: {{ id | replace('light.', '') }}
  entities:
    {% for entity in group.entities %}
    - {{ entity }}
    {% endfor %}
{% endfor %}
