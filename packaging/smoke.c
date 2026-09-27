#include "ui.h"
#include <stdio.h>

static int finish(void *data) { uiQuit(); return 0; }
int main(void) {
    uiInitOptions options = {0};
    const char *error = uiInit(&options);
    if (error != NULL) { fprintf(stderr, "%s\n", error); uiFreeInitError(error); return 1; }
    uiWindow *window = uiNewWindow("libui smoke test", 320, 120, 0);
    uiBox *box = uiNewVerticalBox();
    uiBoxAppend(box, uiControl(uiNewLabel("Updating")), 0);
    uiProgressBar *progress = uiNewProgressBar();
    uiProgressBarSetValue(progress, -1);
    uiBoxAppend(box, uiControl(progress), 0);
    uiMultilineEntry *details = uiNewMultilineEntry();
    uiMultilineEntrySetReadOnly(details, 1);
    uiMultilineEntrySetText(details, "Test details");
    uiBoxAppend(box, uiControl(details), 1);
    uiBoxAppend(box, uiControl(uiNewButton("Close")), 0);
    uiWindowSetChild(window, uiControl(box));
    uiControlShow(uiControl(window));
    uiTimer(100, finish, NULL);
    uiMain();
    uiControlDestroy(uiControl(window));
    uiUninit();
    return 0;
}
