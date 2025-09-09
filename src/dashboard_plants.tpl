views:
  - title: Plants
    sections:
      - type: grid
        cards:
            {% for room in rooms %}
            {% for plant in room.plants %}
          - type: custom:flower-card
            entity: {{ plant.entity }}
            show_bars:
            - moisture
            - temperature
            - humidity
            display_type: compact
            {% endfor %}
            {% endfor %}
