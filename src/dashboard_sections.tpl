views:
  - title: Home
    type: sections
    sections:
      - type: grid
        cards:
          - type: weather-forecast
            show_current: true
            show_forecast: false
            entity: weather.home
            forecast_type: daily
            name: Kingsclere
          - type: vertical-stack
            cards:
              - type: tile
                entity: climate.thermostat
                features:
                  - type: target-temperature
      {% for room in rooms %}
      - type: grid
        cards:
          - type: heading
            heading: {{ room.name }}
            tap_action:
              action: perform-action
              perform_action: input_select.select_option
              target:
                entity_id: input_select.active_room
              data:
                option: {{ room.id }}

            badges:
              - type: entity
                entity: sensor.{{ room.id }}_sensor_temperature

          - type: vertical-stack
            cards:

              {% if room.lights %}
              - type: tile
                entity: {{ room.lights }}
              {% endif %}

              {% if room.fan %}
              - type: tile
                entity: {{ room.fan }}
              {% endif %}

      {% endfor %}
