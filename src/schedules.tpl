{% set daysOfTheWeek = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday"
] -%}

heating:
  name: "Heating"
  icon: mdi:thermometer-auto
  {% for day in daysOfTheWeek %}
  {{ day }}:
    - from: "07:00:00"
      to: "16:00:00"
    - from: "19:00:00"
      to: "22:00:00"
  {% endfor %}
