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
          - entity: input_boolean.presence_automations
            name: Presence-based automation

      - type: tile
        entity: group.living_room_lights
        icon: mdi:floor-lamp
      - type: tile
        entity: group.bedroom_lights
        icon: mdi:floor-lamp
      - type: tile
        entity: group.office_lights
        icon: mdi:floor-lamp
      - type: tile
        entity: group.off_peak
        icon: mdi:home-clock
      - type: tile
        entity: group.fans
        icon: mdi:fan
      - type: tile
        entity: group.presence_home
        icon: mdi:home-account
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
