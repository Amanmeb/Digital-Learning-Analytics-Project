<?php
// Creates custom fields for courses to track language, provider, SNE flag,
// offline availability, and tracking method
// Safe to run multiple times -- skips anything that already exists

define('CLI_SCRIPT', true);
require('/var/www/html/config.php');
require_once($CFG->libdir . '/clilib.php');

cli_writeln('CDLAID Content Fields Setup');
cli_writeln('============================');

$now     = time();
$context = context_system::instance();

// Get or create the custom field category for course content fields
$existing_cat = $DB->get_record('customfield_category', [
    'component' => 'core_course',
    'area'      => 'course',
    'name'      => 'CDLAID Content Information',
]);

if ($existing_cat) {
    $content_category_id = $existing_cat->id;
    cli_writeln('  skip category: CDLAID Content Information');
} else {
    $cat = new stdClass();
    $cat->name              = 'CDLAID Content Information';
    $cat->component         = 'core_course';
    $cat->area              = 'course';
    $cat->itemid            = 0;
    $cat->contextid         = $context->id;
    $cat->description       = '';
    $cat->descriptionformat = 0;
    $cat->sortorder         = 0;
    $cat->timecreated       = $now;
    $cat->timemodified      = $now;
    $content_category_id    = $DB->insert_record('customfield_category', $cat);
    cli_writeln('  created category: CDLAID Content Information (id=' . $content_category_id . ')');
}

$content_fields = [
    [
        'shortname'  => 'cdlaid_language',
        'name'       => 'Language',
        'type'       => 'select',
        'configdata' => json_encode([
            'required'     => 0,
            'uniquevalues' => 0,
            'options'      => "English\nAmharic\nAfan Oromo\nTigrinya\nSomali\nSidamic\nAfar",
            'defaultvalue' => 'English',
            'locked'       => 0,
            'visibility'   => 2,
        ]),
    ],
    [
        'shortname'  => 'cdlaid_provider',
        'name'       => 'Content Provider',
        'type'       => 'select',
        'configdata' => json_encode([
            'required'     => 0,
            'uniquevalues' => 0,
            'options'      => "Ministry of Education Ethiopia\nCamara Education\nPhET University of Colorado\nRachel\nH5P",
            'defaultvalue' => 'Camara Education',
            'locked'       => 0,
            'visibility'   => 2,
        ]),
    ],
    [
        'shortname'  => 'cdlaid_sne_flag',
        'name'       => 'SNE Friendly Content',
        'type'       => 'checkbox',
        'configdata' => json_encode([
            'required'       => 0,
            'uniquevalues'   => 0,
            'checkbydefault' => 0,
            'locked'         => 0,
            'visibility'     => 2,
        ]),
    ],
    [
        'shortname'  => 'cdlaid_offline_available',
        'name'       => 'Available Offline',
        'type'       => 'checkbox',
        'configdata' => json_encode([
            'required'       => 0,
            'uniquevalues'   => 0,
            'checkbydefault' => 1,
            'locked'         => 0,
            'visibility'     => 2,
        ]),
    ],
    [
        'shortname'  => 'cdlaid_tracking_method',
        'name'       => 'Tracking Method',
        'type'       => 'select',
        'configdata' => json_encode([
            'required'     => 0,
            'uniquevalues' => 0,
            'options'      => "xapi_native\nxapi_custom\nscorm\nlti\nurl_only",
            'defaultvalue' => 'xapi_native',
            'locked'       => 0,
            'visibility'   => 2,
        ]),
    ],
];

foreach ($content_fields as $field_def) {
    $existing = $DB->get_record('customfield_field', [
        'shortname'  => $field_def['shortname'],
        'categoryid' => $content_category_id,
    ]);
    if ($existing) {
        cli_writeln('  skip: ' . $field_def['name']);
        continue;
    }
    $field = new stdClass();
    $field->shortname         = $field_def['shortname'];
    $field->name              = $field_def['name'];
    $field->type              = $field_def['type'];
    $field->categoryid        = $content_category_id;
    $field->configdata        = $field_def['configdata'];
    $field->description       = '';
    $field->descriptionformat = 0;
    $field->sortorder         = 0;
    $field->timecreated       = $now;
    $field->timemodified      = $now;
    $DB->insert_record('customfield_field', $field);
    cli_writeln('  created: ' . $field_def['name']);
}

cli_writeln('');
cli_writeln('Done.');
