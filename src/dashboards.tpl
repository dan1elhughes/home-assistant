title: Home
path: home
views:
  - title: Home
    cards:
      - type: entities
        title: Scenes
        entities:
          - scene.everything_on
          - scene.day_mode
          - scene.everything_off
      - type: entities
        entities:
          - group.living_room_lights
          - group.bedroom_lights
          - group.office_lights
          - group.off_peak
          - group.fans
          - group.presence_home
      {% for room in rooms %}
      - type: vertical-stack
        cards:
          - type: markdown
            content: '# {{ room.name }}'
          - square: false
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
  - title: Batteries
    cards:
      - type: entities
        entities:
        {% for sensor in batteries %}
          - entity: {{ sensor }}
        {% endfor %}
