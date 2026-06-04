<?php
// Creates three sample H5P activities in the Grade 1 Mathematics course
// Activities are placeholders -- real H5P content files added later by content team
// xAPI tracking is configured and ready on all three activities

define('CLI_SCRIPT', true);
require('/var/www/html/config.php');
require_once($CFG->libdir . '/clilib.php');
require_once($CFG->dirroot . '/course/lib.php');
require_once($CFG->dirroot . '/mod/h5pactivity/lib.php');

cli_writeln('CDLAID Sample H5P Activities Setup');
cli_writeln('===================================');

// Get Grade 1 Mathematics course
$course = $DB->get_record('course', ['shortname' => 'MATH-GR01']);
if (!$course) {
    cli_writeln('error: MATH-GR01 course not found -- run setup_sample_courses.php first');
    exit(1);
}
cli_writeln('course found: ' . $course->fullname . ' (id=' . $course->id . ')');

// Get the first section of the course
$section = $DB->get_record('course_sections', [
    'course'  => $course->id,
    'section' => 1,
]);
if (!$section) {
    cli_writeln('error: course section 1 not found');
    exit(1);
}

// Get h5pactivity module id
$module = $DB->get_record('modules', ['name' => 'h5pactivity']);
if (!$module) {
    cli_writeln('error: h5pactivity module not found');
    exit(1);
}

$now = time();

$activities = [
    [
        'name'        => 'Memory Game -- Numbers 1 to 10',
        'intro'       => 'Match the numbers with their pictures. A memory game for Grade 1 students.',
        'description' => 'Placeholder -- replace with real H5P memory game file from content team',
    ],
    [
        'name'        => 'Arithmetic Quiz -- Addition and Subtraction',
        'intro'       => 'Practice addition and subtraction with numbers up to 20.',
        'description' => 'Placeholder -- replace with real H5P quiz file from content team',
    ],
    [
        'name'        => 'Crossword -- Number Words',
        'intro'       => 'Spell out number words in this crossword puzzle.',
        'description' => 'Placeholder -- replace with real H5P crossword file from content team',
    ],
];

foreach ($activities as $activity_def) {
    // Check if activity already exists in this course
    $existing = $DB->get_record('h5pactivity', [
        'course' => $course->id,
        'name'   => $activity_def['name'],
    ]);
    if ($existing) {
        cli_writeln('  skip: ' . $activity_def['name']);
        continue;
    }

    // Create h5pactivity record
    $h5p = new stdClass();
    $h5p->course              = $course->id;
    $h5p->name                = $activity_def['name'];
    $h5p->intro               = $activity_def['intro'];
    $h5p->introformat         = 1;
    $h5p->timecreated         = $now;
    $h5p->timemodified        = $now;
    $h5p->grade               = 100;
    $h5p->displayoptions      = 15;
    $h5p->enabletracking      = 1;
    $h5p->grademethod         = 1;
    $h5p->reviewmode          = 1;
    $h5pid = $DB->insert_record('h5pactivity', $h5p);

    // Add to course modules
    $cm = new stdClass();
    $cm->course     = $course->id;
    $cm->module     = $module->id;
    $cm->instance   = $h5pid;
    $cm->section    = $section->id;
    $cm->visible    = 1;
    $cm->visibleold = 1;
    $cm->added      = $now;
    $cm->score      = 0;
    $cm->indent     = 0;
    $cm->completion = 2;
    $cm->completionview = 1;
    $cmid = $DB->insert_record('course_modules', $cm);

    // Add to section sequence
    if ($section->sequence) {
        $section->sequence = $section->sequence . ',' . $cmid;
    } else {
        $section->sequence = $cmid;
    }
    $DB->update_record('course_sections', $section);

    // Rebuild course cache
    rebuild_course_cache($course->id, true);

    cli_writeln('  created: ' . $activity_def['name'] . ' (cmid=' . $cmid . ')');
}

cli_writeln('');
cli_writeln('Done.');
cli_writeln('xAPI tracking enabled on all activities.');
cli_writeln('Replace placeholder activities with real H5P files when content is ready.');
