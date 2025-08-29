require(['driver'], function () {
    function initNetboxWizard() {
        const driver = window.driver.js.driver;

        const driverObj = driver({
            showProgress: true,
            smoothScroll: true,
            steps: [
                {
                    element: '#add-netbox-form',
                    popover: {
                        title: 'Add IP Device',
                        description: 'To enable NAV to collect information from an IP Device, you need to give some basic information about it.',
                        side: 'top'
                    }
                },
                {
                    element: "#id_ip",
                    popover: {
                        title: 'IP Address',
                        description: 'The IP address of the device is needed. Both IPv4 and IPv6 addresses are supported.',
                        side: 'bottom'
                    },
                },
                {
                    element: '#id_room',
                    popover: {
                        title: 'Physical Location',
                        description: `
                            <p>The room is the physical location/wiring closet of the device.
                            You can add more rooms by clicking the <em>"Room"</em> tab.</p>
                            <p>A room can be given a position that enables map placement in some of NAV's tools.</p>
                        `,
                        side: 'bottom'
                    }
                },
                {
                    element: '#id_category',
                    popover: {
                        title: 'Device Category',
                        description: `
                          <p>The category determines how NAV collects data from the device. More
                            information about categories can be found
                            <a href="/doc/intro/getting-started.html#selecting-a-device-category"
                               target="_blank" title="Selecting a device category">in the documentation</a>.
                          </p>
                        `,
                        side: 'bottom'
                    }
                },
                {
                    element: '#id_organization',
                    popover: {
                        title: 'Organization',
                        description: 'The organization indicates who is operationally responsible for the equipment.',
                        side: 'bottom'
                    }
                },
                {
                    element: '#div_id_profiles',
                    popover: {
                        title: 'Management Profile',
                        description: `
                          <p>Selecting a management profile is essential. Without the correct profile,
                            NAV has no means to collect information from the device.</p>
                          <p>Management profiles can be configured in a separate SeedDB tab. For example,
                            you can create an SNMP v2c management profile that can be shared among many
                            of your devices.</p>
                        `,
                        side: 'bottom'
                    },
                },
                {
                    popover: {
                        title: 'Bulk Import Option',
                        description: `
                          <p>
                            If you have a big network with many devices you should check out the
                            <a href="/doc/intro/getting-started.html#importing-multiple-devices-in-bulk" target="_blank"
                               title="Link to bulk import information">bulk import</a> functionality
                            in NAV. Bulk import enables you to import all your devices from comma (or colon) separated text files.
                          </p>
                        `
                    }
                },
                {
                    popover: {
                        title: 'Learn More',
                        description: `
                          <p>
                            If you want more information about using the Seed Database tool to organize your data, please read the
                            <a href="/doc/intro/getting-started.html" title="Getting started" target="_blank">&laquo;Getting started&raquo;</a>
                            and the
                            <a href="/doc/intro/getting-organized.html" title="Getting organized" target="_blank">&laquo;Getting organized&raquo;</a>
                            guides.
                          </p>
                          <p>We wish you a great NAV experience!</p>
                        `
                    }
                }
            ]
        });
        driverObj.drive();
    }

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('guide') === 'true') {
        initNetboxWizard();
    }
});
