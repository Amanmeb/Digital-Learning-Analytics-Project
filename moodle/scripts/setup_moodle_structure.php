<?php
// Creates grade course categories and custom profile fields for students and teachers
// Safe to run multiple times -- skips anything that already exists

define('CLI_SCRIPT', true);
require('/var/www/html/config.php');
require_once($CFG->libdir . '/clilib.php');
require_once($CFG->dirroot . '/course/lib.php');
require_once($CFG->dirroot . '/user/profile/lib.php');

cli_writeln('CDLAID Moodle Structure Setup');
cli_writeln('==============================');

// Create one course category per grade level
cli_writeln('');
cli_writeln('Creating grade course categories...');

$grade_categories = [
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

foreach ($grade_categories as $idnumber => $name) {
    $existing = $DB->get_record('course_categories', ['idnumber' => $idnumber]);
    if ($existing) {
        cli_writeln('  skip: ' . $name);
        continue;
    }
    $category = new stdClass();
    $category->name        = $name;
    $category->idnumber    = $idnumber;
    $category->description = 'Courses for ' . $name;
    $category->parent      = 0;
    $category->visible     = 1;
    $cat = core_course_category::create($category);
    cli_writeln('  created: ' . $name . ' (id=' . $cat->id . ')');
}

// Create student profile field category if it does not exist
cli_writeln('');
cli_writeln('Creating student profile fields...');

$student_category = $DB->get_record('user_info_category', ['name' => 'CDLAID Student Information']);
if (!$student_category) {
    $cat = new stdClass();
    $cat->name      = 'CDLAID Student Information';
    $cat->sortorder = 1;
    $cat->id        = $DB->insert_record('user_info_category', $cat);
    cli_writeln('  created category: CDLAID Student Information');
    $student_category = $DB->get_record('user_info_category', ['id' => $cat->id]);
} else {
    cli_writeln('  skip category: CDLAID Student Information');
}

$student_fields = [
    [
        'shortname'   => 'cdlaid_gender',
        'name'        => 'Gender',
        'datatype'    => 'menu',
        'param1'      => "Male\nFemale\nOther\nPrefer not to say",
        'required'    => 0,
        'visible'     => 2,
        'locked'      => 0,
        'description' => 'Student gender for equity reporting',
    ],
    [
        'shortname'   => 'cdlaid_grade_level',
        'name'        => 'Grade Level',
        'datatype'    => 'menu',
        'param1'      => "Grade 1\nGrade 2\nGrade 3\nGrade 4\nGrade 5\nGrade 6\nGrade 7\nGrade 8\nGrade 9\nGrade 10\nGrade 11\nGrade 12",
        'required'    => 0,
        'visible'     => 2,
        'locked'      => 0,
        'description' => 'Student current grade level',
    ],
    [
        'shortname'   => 'cdlaid_stream',
        'name'        => 'Stream',
        'datatype'    => 'menu',
        'param1'      => "Natural Science\nSocial Science\nVocational\nGeneral",
        'required'    => 0,
        'visible'     => 2,
        'locked'      => 0,
        'description' => 'Student academic stream applies to Grade 11 and 12',
    ],
    [
        'shortname'   => 'cdlaid_special_needs_type',
        'name'        => 'Special Needs Type',
        'datatype'    => 'menu',
        'param1'      => "None\nVisual impairment\nHearing impairment\nCognitive disability\nPhysical disability\nDyslexia\nAutism spectrum\nSpeech and language\nMultiple disabilities",
        'required'    => 0,
        'visible'     => 2,
        'locked'      => 0,
        'description' => 'Student special needs category for inclusion reporting',
    ],
];

foreach ($student_fields as $field) {
    $existing = $DB->get_record('user_info_field', ['shortname' => $field['shortname']]);
    if ($existing) {
        cli_writeln('  skip: ' . $field['name']);
        continue;
    }
    $record = new stdClass();
    $record->shortname         = $field['shortname'];
    $record->name              = $field['name'];
    $record->datatype          = $field['datatype'];
    $record->description       = $field['description'];
    $record->descriptionformat = 1;
    $record->categoryid        = $student_category->id;
    $record->required          = $field['required'];
    $record->visible           = $field['visible'];
    $record->locked            = $field['locked'];
    $record->forceunique       = 0;
    $record->signup            = 0;
    $record->defaultdata       = '';
    $record->defaultdataformat = 0;
    $record->param1            = $field['param1'];
    $record->param2            = '';
    $record->param3            = '';
    $record->param4            = '';
    $record->param5            = '';
    $record->sortorder         = 0;
    $DB->insert_record('user_info_field', $record);
    cli_writeln('  created: ' . $field['name']);
}

// Create teacher profile field category if it does not exist
cli_writeln('');
cli_writeln('Creating teacher profile fields...');

$teacher_category = $DB->get_record('user_info_category', ['name' => 'CDLAID Teacher Information']);
if (!$teacher_category) {
    $cat = new stdClass();
    $cat->name      = 'CDLAID Teacher Information';
    $cat->sortorder = 2;
    $cat->id        = $DB->insert_record('user_info_category', $cat);
    cli_writeln('  created category: CDLAID Teacher Information');
    $teacher_category = $DB->get_record('user_info_category', ['id' => $cat->id]);
} else {
    cli_writeln('  skip category: CDLAID Teacher Information');
}

$teacher_fields = [
    [
        'shortname'   => 'cdlaid_education_level',
        'name'        => 'Education Level',
        'datatype'    => 'menu',
        'param1'      => "Certificate\nDiploma\nBachelor Degree\nMaster Degree\nPhD\nOther",
        'required'    => 0,
        'visible'     => 2,
        'locked'      => 0,
        'description' => 'Teacher highest education level',
    ],
    [
        'shortname'   => 'cdlaid_field_of_study',
        'name'        => 'Field of Study',
        'datatype'    => 'text',
        'param1'      => '100',
        'required'    => 0,
        'visible'     => 2,
        'locked'      => 0,
        'description' => 'Teacher field of study or specialization',
    ],
];

foreach ($teacher_fields as $field) {
    $existing = $DB->get_record('user_info_field', ['shortname' => $field['shortname']]);
    if ($existing) {
        cli_writeln('  skip: ' . $field['name']);
        continue;
    }
    $record = new stdClass();
    $record->shortname         = $field['shortname'];
    $record->name              = $field['name'];
    $record->datatype          = $field['datatype'];
    $record->description       = $field['description'];
    $record->descriptionformat = 1;
    $record->categoryid        = $teacher_category->id;
    $record->required          = $field['required'];
    $record->visible           = $field['visible'];
    $record->locked            = $field['locked'];
    $record->forceunique       = 0;
    $record->signup            = 0;
    $record->defaultdata       = '';
    $record->defaultdataformat = 0;
    $record->param1            = $field['param1'];
    $record->param2            = '';
    $record->param3            = '';
    $record->param4            = '';
    $record->param5            = '';
    $record->sortorder         = 0;
    $DB->insert_record('user_info_field', $record);
    cli_writeln('  created: ' . $field['name']);
}

cli_writeln('');
cli_writeln('Done.');
