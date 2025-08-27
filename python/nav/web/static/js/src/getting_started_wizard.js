define(['driver'], function () {
    'use strict';

    function initGettingStartedWizard() {
        const driver = window.driver.js.driver;

        function handleDone(_element, _step, options) {
            window.scrollTo({ top: 0, behavior: 'smooth' });
            options.driver.destroy();
        }

        const desktopSteps = [
            {
                element: "#getting-started-wizard",
                popover: {
                    title: 'Welcome to NAV!',
                    description: '<p>This 30 second tour will show you the basics.</p>',
                    side: 'bottom'
                }
            },
            {
                element: '#navbar-search-form',
                popover: {
                    title: 'Search',
                    description: '<p>Search for IP Devices, rooms, interfaces, VLANs and so forth here.</p>',
                    side: 'bottom'
                }
            },
            {
                element: '#megadroptoggler',
                popover: {
                    title: 'Your Tools',
                    description: '<p>All your tools can be found here.</p>',
                    side: 'bottom'
                }
            },
            {
                element: '#widgets-action-add',
                popover: {
                    title: 'Widgets',
                    description: '<p>More widgets can be added by using this button.</p>',
                    side: 'left'
                }
            },
            {
                element: '.navlet-action-group',
                popover: {
                    title: 'Widget Controls',
                    description: '<p>Move or remove the widget. In many cases you will also see an edit option so that you can personalize the display.</p>',
                    side: 'bottom'
                }
            },
            {
                element: '#footer-documentation-link',
                popover: {
                    description: '<p>Our documentation and wiki pages are stuffed with more information about NAV. A <a href="/doc" title="local documentation">local copy of the documentation</a> is also available.</p>',
                    side: 'top',
                    onNextClick: handleDone
                }
            }
        ];

        const mobileSteps = [
            {
                popover: {
                    title: 'Welcome to NAV!',
                    description: '<p>This 30 second tour will show you the basics.</p>'
                }
            },
            {
                element: '.toggle-topbar',
                popover: {
                    title: 'Search and Tools',
                    description: '<p>Open the menu on the top right to get access to search and tools.</p>',
                    side: 'bottom'
                }
            },
            {
                element: '.navlet-action-group',
                popover: {
                    title: 'Widget Controls',
                    description: '<p>Move or remove the widget by using the icons. In many cases you will also see an edit option so that you can personalize the display.</p>',
                    side: 'bottom'
                }
            },
            {
                element: '#footer-documentation-link',
                popover: {
                    description: '<p>Our documentation and wiki pages are stuffed with more information about NAV. A <a href="/doc" title="local documentation">local copy of the documentation</a> is also available.</p>',
                    side: 'top',
                    onNextClick: handleDone
                }
            }
        ];

        const isMobile = window.innerWidth <= 768;
        const steps = isMobile ? mobileSteps : desktopSteps;

        const driverObj = driver({
            showProgress: true,
            smoothScroll: true,
            steps: steps
        });

        driverObj.drive();
    }

    return {
        start: initGettingStartedWizard
    }
})
