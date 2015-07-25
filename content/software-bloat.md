Title: Software bloat
Date: 2015-07-25 19:53
Modified: 2015-07-25 22:56

This post is inspired by an [article written by Maciej Cegłowski](http://idlewords.com/talks/web_design_first_100_years.htm) on the subject of wastefulness in modern software.

A 1.67 GHz single-core processor and 2 GB of DDR memory are a pittance compared to modern hardware, yet this 'archaic' machine is still capable of basic audio editing in Logic Pro, and other seemingly complex tasks such as software compilation etc. Despite all this, visiting the [Daily Mail website](#) brings this machine crashing to its knees.

Once the flagship of Apple's 2005 product lineup, the PowerBook G4 becomes completely unresponsive for a good few seconds trying to load any modern website which hasn't been designed with resource-starved devices in mind. While it's never true to say that technology needn't progress any further than its current state, it's at the point where what we have is *good enough* for the average user. Tasks such as watching
videos, social media, composing emails, general browsing and word processing more or less cover the spectrum of typical computer usage. The most challenging of webpages might have a combination of high-definition video, images, and multiple scripts to pull in dynamic content and tie everything together. Unfortunately for the PowerBook G4, it came just before online video content became fully mainstream. Thankfully all modern devices are blessed with dedicated H.264 decoders which make light work of all but the highest-resolution video. Expecting a decade-old machine to be able to handle something as intensive as high-quality video would just be unreasonable, but I don't feel that it's unfair to ask that it be able to handle the most basic of online tasks such as reading the news and composing email.

### Case study: Daily Mail

Using the Internet Archive we can track how pageload speeds and download sizes have increased over the past decade or so. It should be noted that pageload speed cannot be used to reliably determine bloat because archive.org's servers have a large impact on this. Download sizes however, have stayed more or less the same between the original page and the captured snapshots presented here.

[In 2004]({filename}/images/dailymail_homepage_2004.jpg), the Daily Mail weighed around 340 KB – mostly CSS styling and small photographs, with a few icons and scripts; it was high functional, containing around 10 short summaries, and links to various other daily headlines.

![Daily Mail size per content type in 2004]({filename}/images/dailymail_content_2004.png)

A decade later, it has grown to an enormous *13.7 MB* and takes over 16 seconds to load (2013 MacBook Air, 5 Mb/s downlink). Clicking on the main article downloads an additional 10.1 MB of data. One change is instantly obvious – the sheer quantity of content has grown exponentially. To illustrate how ridiculous this is, [here is a full-length image of today's Daily Mail homepage]({filename}/images/dailymail_homepage_full.jpg). Printing this page would use *29 sheets* of A4 paper. Most astonishing is the fact that visiting the homepage on a phone loads the desktop version by default. There's absolutely no way that the average user is going to read all of that content in an average sitting. 'Infinite scrolling' – whereby a new chunk of content is dynamically loaded in once the user scrolls further down the page – has been practical for years; not only is this a complete waste of processing resources on the client-side, but it also wastes server resources, churning out so much data, despite the fact that only some of it will ever be consumed.

![Daily Mail size per content type in 2015]({filename}/images/dailymail_content_present.png)

As expected, we see that the amount of image data has increased dramatically, making up a disproportionately high percentage of all content. Also surprising is the sheer amount of JavaScript being loaded – 1.3 MB. The Daily Mail homepage is almost entirely static – what on earth is 1.3 MB of JS code being used for? Here's what's being loaded:

* `AjaxPoll.js`- Daily Mail daily poll
* `engine.js` - Direct Web Remoting
* `log.pinterest.com` - Unknown, Pinterest
* `pid=a6f7193ab778cdd9bb61ba871b8de7ca` - Crowd Control analytics
* `BrightcoveExperiences.js` - Brightcove video platform
* `trinity.js` - Sonobi APEX advertising
* `cb=gapi.loaded_0` - Unknown Google API
* `plusone.js` - Google Plus API
* `cygnus` - Casalmedia advertising
* `pinit_main.js` - Pinterest API
* `pinit.js` - Pinterest API
* `beacon.js` - ScorecardResearch tracking
* `fpc=y` - Crowd Control analytics
* `impl.169-3-RELEASE.js` - Taboola advertising
* `loader.js` - Taboola advertising
* `all.js` - Facebook SDK
* `fbds.js` - Facebook tracking
* `actvt` - Audience Science tracking
* `channels.cgi` - Unknown Daily Mail
* `dm.js` - Optimax Media Delivery advertising
* `gw.js` - Audience Science advertising
* `cross-check.js` - Unknown Taboola
* `jstag` - OpenX advertising
* `expansion_embed.js` - Google advertising
* `osd.js` - Google advertising
* `pubads_impl_68r2.js` - Google advertising
* `226531683.js` - Audience Science tracking
* `widgets.js` - Twitter widget
* `rta.js` - Criteo advertising
* `async_bundle--.js` - Daily Mail tracking
* `fff.js` - Daily Mail mobile UI?
* `googleads--.js` - Google Ads
* `sync_bundle.js` - Unknown, Daily Mail
* `gpt.js` - Google Publisher Tags

Granted, none of these items were researched very thoroughly; nonetheless, it's a clear abuse of JavaScript for tracking and advertising purposes.

In comparison, the [BBC homepage from 2004]({filename}/images/bbc_homepage_2004.jpg) weighs in at just over 300 KB, growing to [2.3 MB in 2015]({filename}/images/bbc_homepage_present.jpg). While slightly higher than desirable, 2.3 MB seems very reasonable given that we're talking about media websites.

### Change has to start somewhere

The article that this post is based on is of particular interest given that the author, Cegłowski, is the sole developer behind [Pinboard](https://pinboard.in), a website – the continuation of an old family business – which allows users to archive and search through interesting links. The design is astoundingly simple, yet is perfectly functional and never lacking; it is a shining example of the approach I would like to see more developers taking. While mainstream websites and software will keep pandering to the endless and unecessary bells-and-whistles of the mass-market, it would be nice to think that a small handful of developers can design things that function perfectly fine without, just as in the days before cheap hardware was readily available and every drop of performance had to be coaxed out.
