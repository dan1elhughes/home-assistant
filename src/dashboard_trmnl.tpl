views:
  - type: sections
    theme: Graphite E-ink Light
    badges:
      {% for w in waste_collections %}
      - type: entity
        show_name: true
        show_state: true
        entity: {{ w.entity }}
        name: {{ w.name }}
        visibility:
          - condition: numeric_state
            entity: {{ w.entity }}_days_until_collection
            below: 3
      {% endfor %}

    sections:
      - type: grid
        column_span: 4
        cards:
          - type: weather-forecast
            grid_options:
               columns: full
            show_current: false
            show_forecast: true
            entity: weather.home
            forecast_type: hourly
            forecast_slots: 8
            round_temperature: true

      - type: grid
        column_span: 4
        cards:
          - type: custom:calendar-card-pro
            entities:
            - calendar.k_d
            days_to_show: 2
            show_location: true
