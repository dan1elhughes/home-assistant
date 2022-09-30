title: Home
path: home
views:
  - title: Batteries
    cards:
      - type: entities
        entities:
        {% for sensor in batteries %}
          - entity: {{ sensor }}
        {% endfor %}
  - title: Environment
    cards:
      {% for room in rooms %}
      - type: vertical-stack
        cards:
          - type: markdown
            content: '# {{ room.name }}'
          - square: true
            columns: 2
            type: grid
            cards:
              - hours_to_show: 24
                graph: line
                type: sensor
                entity: "{{room.sensorPrefix}}temperature"
                detail: 1
                name: Temperature
              - type: gauge
                entity: "{{room.sensorPrefix}}humidity"
                name: Humidity
      {% endfor %}
