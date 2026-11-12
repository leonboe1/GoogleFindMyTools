FROM selenium/standalone-chrome:latest

USER root

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/Auth && chown -R seluser:seluser /app
RUN chown -R seluser:seluser /home/seluser

COPY docker-entrypoint.sh /opt/bin/gfm-entrypoint.sh
RUN chmod +x /opt/bin/gfm-entrypoint.sh

USER seluser

ENTRYPOINT ["/opt/bin/gfm-entrypoint.sh"]
