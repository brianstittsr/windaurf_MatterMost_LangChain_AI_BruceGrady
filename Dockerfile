FROM mattermost/mattermost-team-edition:latest

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

# Use the default entrypoint from the base image
ENTRYPOINT ["/entrypoint.sh"]
CMD ["mattermost"]
