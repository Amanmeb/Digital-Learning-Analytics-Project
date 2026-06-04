<?php
// Creates one sample Mathematics course per grade for testing
// Each course is placed in the correct grade category
// Safe to run multiple times -- skips existing courses

define('CLI_SCRIPT', true);
require('/var/www/html/config.php');
require_once($CFG->libdir . '/clilib.php');
require_once($CFG->dirroot . '/course/lib.php');

cli_writeln('CDLAID Sample Courses Setup');
cli_writeln('============================');

$grades = [
    'GR01' => 'Grade 1',
    'GR02' => 'Grade 2',
    'GR03' => 'Grade 3',
    'GR04' => 'Grade 4',
    'GR05' => 'Grade 5',
    'GR06' => 'Grade 6',
    'GR07' => 'Grade 7',
    'GR08' => 'Grade 8',
    'GR09' => 'Grade 9',
    'GR10' => 'Grade 10',
    'GR11' => 'Grade 11',
    'GR12' => 'Grade 12',
];

foreach ($grades as $grade_idnumber => $grade_name) {
    $shortname = 'MATH-' . $grade_idnumber;
    $fullname  = 'Mathematics -- ' . $grade_name;

    // Check if course already exists
    $existing = $DB->get_record('course', ['shortname' => $shortname]);
    if ($existing) {
        cli_writeln('  skip: ' . $fullname);
        continue;
    }

    // Get the grade category id
    $category = $DB->get_record('course_categories', ['idnumber' => $grade_idnumber]);
    if (!$category) {
        cli_writeln('  error: category not found for ' . $grade_idnumber);
        continue;
    }

    // Build course object
    $course = new stdClass();
    $course->fullname        = $fullname;
    $course->shortname       = $shortname;
    $course->category        = $category->id;
    $course->idnumber        = 'CDLAID-' . $shortname;
    $course->summary         = 'Mathematics sample course for ' . $grade_name;
    $course->summaryformat   = 1;
    $course->format          = 'topics';
    $course->visible         = 1;
    $course->numsections     = 10;
    $course->startdate       = mktime(0, 0, 0, 9, 1, 2025);
    $course->enddate         = mktime(0, 0, 0, 7, 31, 2026);
    $course->lang            = 'en';
    $course->enablecompletion = 1;

    $created = create_course($course);
    cli_writeln('  created: ' . $fullname . ' (id=' . $created->id . ')');

    // Set custom fields for this course
    $now = time();

    // Get custom field ids
    $fields = [
        'cdlaid_language'        => 'English',
        'cdlaid_provider'        => 'Camara Education',
        'cdlaid_sne_flag'        => 0,
        'cdlaid_offline_available' => 1,
        'cdlaid_tracking_method' => 'xapi_native',
    ];

    foreach ($fields as $shortname_field => $value) {
        $field = $DB->get_record('customfield_field', ['shortname' => $shortname_field]);
        if (!$field) {
            continue;
        }
        $data = new stdClass();
        $data->fieldid      = $field->id;
        $data->instanceid   = $created->id;
        $data->value        = $value;
        $data->valueformat  = 0;
        $data->timecreated  = $now;
        $data->timemodified = $now;
        $DB->insert_record('customfield_data', $data);
    }
}

cli_writeln('');
cli_writeln('Done.');
