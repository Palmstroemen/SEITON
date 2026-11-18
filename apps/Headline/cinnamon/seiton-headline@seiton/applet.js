// SEITON's Headline in Cinnamon's panel (apps/Scope/Designdocument Headline.md, step 4).
// Only a button with SEITON's box: a click asks the Headline to open its panel at the
// button, towards the room (above a panel at the bottom). Everything else is the Headline's.
const Applet = imports.ui.applet;
const Util = imports.misc.util;

// Written by the installer (installer/seiton_install.py): the Headline's launcher.
const LAUNCHER = "__LAUNCHER__";

class SeitonHeadlineApplet extends Applet.IconApplet {
    constructor(metadata, orientation, panelHeight, instanceId) {
        super(orientation, panelHeight, instanceId);
        this.set_applet_icon_path(metadata.path + "/icon.svg");
        this.set_applet_tooltip("SEITON");
    }

    on_applet_clicked(event) {
        // Where the button is on the screen, in device pixels (the Headline turns them into
        // Qt's logical ones).
        const [x, y] = this.actor.get_transformed_position();
        const [width, height] = this.actor.get_transformed_size();
        const anchor = [x, y, width, height].map(value => Math.round(value)).join(",");
        Util.spawn([LAUNCHER, "--panel", "--anchor", anchor]);
    }
}

function main(metadata, orientation, panelHeight, instanceId) {
    return new SeitonHeadlineApplet(metadata, orientation, panelHeight, instanceId);
}
