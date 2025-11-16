views:
  - title: Plants
    sections:
      {% for room in rooms %}
      {% for plant in room.plants %}
      - type: grid
        cards:
          - type: custom:flower-card
            entity: {{ plant.entity }}
            show_bars:
            - moisture
            - temperature
            - humidity
            display_type: compact

          - type: tile
            entity: automation.plant_monitor_{{ plant.entity | replace('.', '_') }}
            name: Automation

          - type: tile
            entity: {{ plant.indicator }}
            name: Light
      {% endfor %}
      {% endfor %}
