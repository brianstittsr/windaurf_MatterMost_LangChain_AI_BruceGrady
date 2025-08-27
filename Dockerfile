FROM mattermost/mattermost-team-edition:latest

# Install curl for health checks
USER root
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
USER 2000

# Set environment variables
ENV MM_SQLSETTINGS_DRIVERNAME=postgres
ENV MM_SQLSETTINGS_DATASOURCE=""
ENV MM_SERVICESETTINGS_SITEURL=""
ENV MM_SERVICESETTINGS_LISTENADDRESS=":8000"
ENV MM_SERVICESETTINGS_ENABLELOCALMODE=false
ENV MM_SERVICESETTINGS_ENABLEDEVELOPER=false
ENV MM_SERVICESETTINGS_ENABLEINCOMINGWEBHOOKS=true
ENV MM_SERVICESETTINGS_ENABLEOUTGOINGWEBHOOKS=true
ENV MM_SERVICESETTINGS_ENABLECOMMANDS=true

# Expose port
EXPOSE 8000

# Health check for Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v4/system/ping || exit 1

# Use the correct command for Mattermost
CMD ["mattermost"]
