FROM mattermost/mattermost-team-edition:latest

# Set environment variables
ENV MM_SQLSETTINGS_DRIVERNAME=postgres
ENV MM_SQLSETTINGS_DATASOURCE=""
ENV MM_SERVICESETTINGS_SITEURL=""
ENV MM_SERVICESETTINGS_LISTENADDRESS=":8000"
ENV MM_SERVICESETTINGS_ENABLELOCALMODE=false
ENV MM_SERVICESETTINGS_ENABLEDEVELOPER=false

# Expose port
EXPOSE 8000

# Use the default entrypoint from the base image
ENTRYPOINT ["/entrypoint.sh"]
CMD ["mattermost"]
