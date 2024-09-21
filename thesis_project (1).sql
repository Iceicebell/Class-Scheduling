-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Sep 19, 2024 at 10:14 AM
-- Server version: 10.4.24-MariaDB
-- PHP Version: 8.1.6

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `thesis_project`
--

-- --------------------------------------------------------

--
-- Table structure for table `allocations`
--

CREATE TABLE `allocations` (
  `id` int(11) NOT NULL,
  `course_id` int(11) DEFAULT NULL,
  `room_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `classrooms`
--

CREATE TABLE `classrooms` (
  `room_id` int(11) NOT NULL,
  `room_no` int(255) NOT NULL,
  `capacity` int(200) NOT NULL,
  `type` varchar(100) NOT NULL,
  `floor_level` int(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `classrooms`
--

INSERT INTO `classrooms` (`room_id`, `room_no`, `capacity`, `type`, `floor_level`) VALUES
(3, 100, 20, 'networking', 1);

-- --------------------------------------------------------

--
-- Table structure for table `courses`
--

CREATE TABLE `courses` (
  `course_id` int(11) NOT NULL,
  `course_code` varchar(255) NOT NULL,
  `course_name` varchar(255) NOT NULL,
  `course_block` varchar(50) DEFAULT NULL,
  `course_type` enum('Lecture','Comp Laboratory','Engineering Laboratory','Networking') NOT NULL,
  `course_level` enum('1st Year','2nd Year','3rd Year','4th Year') NOT NULL,
  `units` decimal(5,2) NOT NULL,
  `hours_per_week` decimal(50,2) NOT NULL,
  `program_id` int(11) DEFAULT NULL,
  `faculty_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `courses`
--

INSERT INTO `courses` (`course_id`, `course_code`, `course_name`, `course_block`, `course_type`, `course_level`, `units`, `hours_per_week`, `program_id`, `faculty_id`) VALUES
(21, 'CC103', 'DATA STRUCTURES AND ALGORITHMS', 'A', 'Lecture', '2nd Year', '5.00', '5.00', 1, 12),
(22, 'CS PC 211', 'DISCRETE STRUCTURES 2', 'A', 'Lecture', '2nd Year', '3.00', '3.00', 1, 13),
(23, 'CS PC 212', 'OBJECT ORIENTED PROGRAMMING', 'A', 'Comp Laboratory', '2nd Year', '3.00', '3.00', 1, 12),
(24, 'CS PC ELEC 01', 'FUNDAMENTALS OF HUMAN COMPUTER INTERACTION', 'A', 'Comp Laboratory', '2nd Year', '3.00', '3.00', 1, 14),
(25, 'MATH 100', 'CALCULUS', 'A', 'Lecture', '2nd Year', '3.00', '3.00', 1, 15),
(26, 'CC103', 'DATA STRUCTURES AND ALGORITHMS', 'A', 'Lecture', '2nd Year', '3.00', '5.00', 2, 12),
(27, 'IT ELEC 01', 'IT ELECTIVE 1', 'A', 'Comp Laboratory', '2nd Year', '3.00', '3.00', 2, 16),
(28, 'IT PC 212', 'RELATED LEARNING EXPERIENCE', 'A', 'Lecture', '2nd Year', '1.00', '1.00', 1, 12),
(29, 'IT PC 212', 'RELATED LEARNING EXPERIENCE', 'A', 'Lecture', '2nd Year', '1.00', '1.00', 2, 12),
(30, 'IT PC 213', 'NETWORKING 1', 'A', 'Comp Laboratory', '2nd Year', '3.00', '3.00', 2, 17),
(31, 'IT PC 211', 'INTRODUCTION TO HUMAN COMPUTER INTERACTION', 'A', 'Comp Laboratory', '2nd Year', '3.00', '3.00', 2, 18),
(32, 'AcctgEd03', 'Law o Obligations and contracts', 'A', 'Lecture', '1st Year', '3.00', '3.00', 8, 21),
(33, 'AcctgEd04', 'Conceptual Framework and Accounting Standards', 'A', 'Lecture', '1st Year', '3.00', '3.00', 8, 20),
(34, 'CBME01', 'Operation Management and TQM', 'A', 'Lecture', '1st Year', '3.00', '3.00', 8, 20),
(50, 'cs1', 'computer science', 'A', 'Lecture', '2nd Year', '5.00', '12.00', 17, 27),
(51, 'nursing1', 'nursing1', 'A', 'Lecture', '1st Year', '3.00', '4.00', 17, 27),
(52, 'nursing2', 'nursing2', 'A', 'Lecture', '1st Year', '3.00', '5.00', 17, 34),
(53, 'nursing3', 'nursing3', 'A', 'Lecture', '1st Year', '3.00', '5.00', 17, 27);

--
-- Triggers `courses`
--
DELIMITER $$
CREATE TRIGGER `update_faculty_used_units` AFTER DELETE ON `courses` FOR EACH ROW BEGIN
    UPDATE faculties
    SET faculty_used_units = faculty_used_units - OLD.units
    WHERE faculty_id = OLD.faculty_id;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `created_schedules`
--

CREATE TABLE `created_schedules` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `section_id` int(11) DEFAULT NULL,
  `course_id` int(11) DEFAULT NULL,
  `day` varchar(10) DEFAULT NULL,
  `start_hour` decimal(4,2) DEFAULT NULL,
  `duration` decimal(4,2) DEFAULT NULL,
  `course_code` varchar(10) DEFAULT NULL,
  `course_block` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `created_schedules`
--

INSERT INTO `created_schedules` (`id`, `user_id`, `section_id`, `course_id`, `day`, `start_hour`, `duration`, `course_code`, `course_block`) VALUES
(69, 19, 2, -1, 'Monday', '8.50', '1.50', 'Unavailabl', 'None'),
(70, 19, 2, -1, 'Wednesday', '8.50', '1.50', 'Unavailabl', 'None'),
(71, 19, 2, -1, 'Monday', '10.00', '1.50', 'Unavailabl', 'None'),
(72, 19, 2, -1, 'Wednesday', '10.00', '1.50', 'Unavailabl', 'None'),
(73, 19, 2, -1, 'Tuesday', '16.00', '1.50', 'Unavailabl', 'None'),
(74, 19, 2, -1, 'Friday', '16.00', '1.50', 'Unavailabl', 'None'),
(75, 19, 2, -1, 'Thursday', '13.00', '7.00', 'Unavailabl', 'None'),
(76, 19, 2, 21, 'Thursday', '17.50', '2.50', 'CC103', 'A'),
(77, 19, 2, 21, 'Saturday', '17.50', '2.50', 'CC103', 'A'),
(78, 19, 2, 22, 'Thursday', '10.00', '1.50', 'CS PC 211', 'A'),
(79, 19, 2, 22, 'Saturday', '10.00', '1.50', 'CS PC 211', 'A'),
(80, 19, 2, 24, 'Thursday', '14.00', '1.50', 'CS PC ELEC', 'A'),
(81, 19, 2, 24, 'Saturday', '14.00', '1.50', 'CS PC ELEC', 'A'),
(82, 19, 2, 25, 'Tuesday', '10.00', '1.50', 'MATH 100', 'A'),
(83, 19, 2, 25, 'Friday', '10.00', '1.50', 'MATH 100', 'A'),
(84, 19, 2, 28, 'Monday', '15.00', '1.00', 'IT PC 212', 'A'),
(85, 19, 2, 23, 'Tuesday', '8.00', '1.50', 'CS PC 212', 'A'),
(86, 19, 2, 23, 'Friday', '8.00', '1.50', 'CS PC 212', 'A'),
(87, 19, 3, -1, 'Tuesday', '7.00', '1.50', 'Unavailabl', 'None'),
(88, 19, 3, -1, 'Friday', '7.00', '1.50', 'Unavailabl', 'None'),
(89, 19, 3, -1, 'Tuesday', '16.00', '1.50', 'Unavailabl', 'None'),
(90, 19, 3, -1, 'Friday', '16.00', '1.50', 'Unavailabl', 'None'),
(91, 19, 3, -1, 'Thursday', '13.00', '3.00', 'Unavailabl', 'None'),
(92, 19, 3, -1, 'Monday', '15.00', '1.50', 'Unavailabl', 'None'),
(93, 19, 3, -1, 'Wednesday', '15.00', '1.50', 'Unavailabl', 'None'),
(94, 19, 3, 26, 'Thursday', '17.50', '2.50', 'CC103', 'A'),
(95, 19, 3, 26, 'Saturday', '17.50', '2.50', 'CC103', 'A'),
(96, 19, 3, 29, 'Monday', '15.00', '1.00', 'IT PC 212', 'A'),
(97, 19, 3, 27, 'Thursday', '16.00', '1.50', 'IT ELEC 01', 'A'),
(98, 19, 3, 27, 'Saturday', '16.00', '1.50', 'IT ELEC 01', 'A'),
(99, 19, 3, 30, 'Monday', '8.00', '1.50', 'IT PC 213', 'A'),
(100, 19, 3, 30, 'Wednesday', '8.00', '1.50', 'IT PC 213', 'A'),
(101, 19, 3, 31, 'Thursday', '9.00', '1.50', 'IT PC 211', 'A'),
(102, 19, 3, 31, 'Saturday', '9.00', '1.50', 'IT PC 211', 'A'),
(138, 27, 10, -1, 'Monday', '7.00', '1.50', 'Unavailabl', 'None'),
(139, 27, 10, 51, 'Thursday', '17.00', '2.00', 'nursing1', 'A'),
(140, 27, 10, 51, 'Saturday', '17.00', '2.00', 'nursing1', 'A'),
(141, 27, 10, 52, 'Tuesday', '9.00', '2.50', 'nursing2', 'A'),
(142, 27, 10, 52, 'Friday', '9.00', '2.50', 'nursing2', 'A'),
(143, 27, 10, 53, 'Tuesday', '16.00', '2.50', 'nursing3', 'A'),
(144, 27, 10, 53, 'Friday', '16.00', '2.50', 'nursing3', 'A');

-- --------------------------------------------------------

--
-- Table structure for table `faculties`
--

CREATE TABLE `faculties` (
  `faculty_id` int(11) NOT NULL,
  `first_name` varchar(255) NOT NULL,
  `last_name` varchar(255) NOT NULL,
  `faculty_type` enum('Full Time','Part Time') NOT NULL,
  `faculty_units` decimal(5,2) NOT NULL,
  `department` varchar(255) NOT NULL,
  `faculty_used_units` float NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `faculties`
--

INSERT INTO `faculties` (`faculty_id`, `first_name`, `last_name`, `faculty_type`, `faculty_units`, `department`, `faculty_used_units`) VALUES
(12, 'Mary Grace', 'Enriquez', 'Full Time', '25.00', 'CSIT', 11),
(13, 'Rhodora Faye', 'Brosas', 'Full Time', '25.00', 'CSIT', 3),
(14, 'Relian', 'Cadubla', 'Full Time', '25.00', 'CSIT', 3),
(15, 'Rey', 'Literal', 'Part Time', '18.00', 'CSIT', 3),
(16, 'Jp', 'Serrano', 'Full Time', '25.00', 'CSIT', 3),
(17, 'Jay ', 'Benaraba', 'Full Time', '25.00', 'CSIT', 3),
(18, 'Shaira', 'Pepeno', 'Full Time', '25.00', 'CSIT', 3),
(19, 'Rey', 'Literal', 'Part Time', '16.00', 'CSIT', 0),
(20, 'Daria', 'Labalan', 'Full Time', '18.00', 'SBMA', 6),
(21, 'Stephen', 'Bucay', 'Full Time', '24.00', 'SBMA', 3),
(27, 'asd', 'asd', 'Full Time', '12.00', 'SON', 11),
(30, 'understanding', 'teacher', 'Full Time', '25.00', 'GENED', 12),
(31, 'math', 'teacher', 'Full Time', '25.00', 'GENED', 9),
(32, 'communicating', 'teacher', 'Full Time', '25.00', 'GENED', 6),
(33, 'science', 'teacher', 'Part Time', '12.00', 'GENED', 9),
(34, '123', '123', 'Full Time', '12.00', 'SON', 3);

-- --------------------------------------------------------

--
-- Table structure for table `gened_courses`
--

CREATE TABLE `gened_courses` (
  `course_id` int(11) NOT NULL,
  `course_code` varchar(255) NOT NULL,
  `course_name` varchar(255) NOT NULL,
  `course_block` varchar(50) DEFAULT NULL,
  `units` decimal(5,2) NOT NULL,
  `hours_per_week` decimal(50,2) NOT NULL,
  `faculty_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `gened_courses`
--

INSERT INTO `gened_courses` (`course_id`, `course_code`, `course_name`, `course_block`, `units`, `hours_per_week`, `faculty_id`) VALUES
(5, 'GE 01', 'UNDERSTANDING THE SELF', 'A', '3.00', '3.00', 30),
(6, 'GE 04', 'MATHEMATICS IN THE MODERN WORLD', 'A', '3.00', '3.00', 31),
(7, 'GE 05', 'PURPOSIVE COMMUNICATION', 'A', '3.00', '3.00', 32),
(8, 'GE 07', 'SCIENCE, TECHNOLOGY AND SOCIETY', 'A', '3.00', '3.00', 33),
(9, 'GE 01', 'UNDERSTANDING THE SELF', 'B', '3.00', '3.00', 30),
(10, 'GE 01', 'UNDERSTANDING THE SELF', 'C', '3.00', '3.00', 30),
(11, 'GE 04', 'MATHEMATICS IN THE MODERN WORLD', 'B', '3.00', '3.00', 31),
(12, 'GE 04', 'MATHEMATICS IN THE MODERN WORLD', 'C', '3.00', '3.00', 31),
(13, 'GE 05', 'PURPOSIVE COMMUNICATION', 'B', '3.00', '3.00', 32),
(14, 'GE 05', 'PURPOSIVE COMMUNICATION', 'C', '3.00', '3.00', 32),
(15, 'GE 07', 'SCIENCE, TECHNOLOGY AND SOCIETY', 'B', '3.00', '3.00', 33),
(16, 'GE 07', 'SCIENCE, TECHNOLOGY AND SOCIETY', 'C', '3.00', '3.00', 33);

--
-- Triggers `gened_courses`
--
DELIMITER $$
CREATE TRIGGER `update faculty units` AFTER DELETE ON `gened_courses` FOR EACH ROW BEGIN
    UPDATE faculties
    SET faculty_used_units = faculty_used_units - OLD.units
    WHERE faculty_id = OLD.faculty_id;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `gened_solutions`
--

CREATE TABLE `gened_solutions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `course_id` int(11) DEFAULT NULL,
  `day` varchar(10) DEFAULT NULL,
  `start_hour` decimal(4,2) DEFAULT NULL,
  `duration` decimal(4,2) DEFAULT NULL,
  `course_code` varchar(10) DEFAULT NULL,
  `course_block` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `gened_solutions`
--

INSERT INTO `gened_solutions` (`id`, `user_id`, `course_id`, `day`, `start_hour`, `duration`, `course_code`, `course_block`) VALUES
(311, 29, 5, 'Tuesday', '14.00', '1.50', 'GE 01', 'A'),
(312, 29, 5, 'Friday', '14.00', '1.50', 'GE 01', 'A'),
(313, 29, 6, 'Tuesday', '11.00', '1.00', 'GE 04', 'A'),
(314, 29, 6, 'Friday', '11.00', '1.00', 'GE 04', 'A'),
(315, 29, 7, 'Thursday', '13.00', '1.50', 'GE 05', 'A'),
(316, 29, 7, 'Saturday', '13.00', '1.50', 'GE 05', 'A'),
(317, 29, 8, 'Monday', '8.00', '1.50', 'GE 07', 'A'),
(318, 29, 8, 'Wednesday', '8.00', '1.50', 'GE 07', 'A'),
(319, 29, 9, 'Tuesday', '17.00', '1.50', 'GE 01', 'B'),
(320, 29, 9, 'Friday', '17.00', '1.50', 'GE 01', 'B'),
(321, 29, 10, 'Monday', '15.00', '1.50', 'GE 01', 'C'),
(322, 29, 10, 'Wednesday', '15.00', '1.50', 'GE 01', 'C'),
(323, 29, 11, 'Thursday', '10.00', '1.50', 'GE 04', 'B'),
(324, 29, 11, 'Saturday', '10.00', '1.50', 'GE 04', 'B'),
(325, 29, 12, 'Monday', '9.00', '1.50', 'GE 04', 'C'),
(326, 29, 12, 'Wednesday', '9.00', '1.50', 'GE 04', 'C'),
(327, 29, 13, 'Tuesday', '11.00', '1.00', 'GE 05', 'B'),
(328, 29, 13, 'Friday', '11.00', '1.00', 'GE 05', 'B'),
(329, 29, 14, 'Tuesday', '16.00', '1.50', 'GE 05', 'C'),
(330, 29, 14, 'Friday', '16.00', '1.50', 'GE 05', 'C'),
(331, 29, 15, 'Saturday', '9.00', '1.50', 'GE 07', 'B'),
(332, 29, 15, 'Tuesday', '9.00', '1.50', 'GE 07', 'B'),
(333, 29, 16, 'Thursday', '13.00', '1.50', 'GE 07', 'C'),
(334, 29, 16, 'Saturday', '13.00', '1.50', 'GE 07', 'C');

-- --------------------------------------------------------

--
-- Table structure for table `programs`
--

CREATE TABLE `programs` (
  `program_id` int(11) NOT NULL,
  `program_name` varchar(255) NOT NULL,
  `user_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `programs`
--

INSERT INTO `programs` (`program_id`, `program_name`, `user_id`) VALUES
(1, 'BSCS', 19),
(2, 'BSIT', 19),
(8, 'BSA', 26),
(17, 'SON', 27);

-- --------------------------------------------------------

--
-- Table structure for table `room_courses`
--

CREATE TABLE `room_courses` (
  `course_id` int(11) NOT NULL,
  `course_code` varchar(100) NOT NULL,
  `capacity` int(255) NOT NULL,
  `type` varchar(100) NOT NULL,
  `block` varchar(20) NOT NULL,
  `department` varchar(100) NOT NULL,
  `start_time` decimal(50,2) NOT NULL,
  `end_time` decimal(50,2) NOT NULL,
  `day` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `sections`
--

CREATE TABLE `sections` (
  `section_id` int(11) NOT NULL,
  `section_name` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `capacity` int(50) NOT NULL,
  `year_level` varchar(100) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `program_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `sections`
--

INSERT INTO `sections` (`section_id`, `section_name`, `created_at`, `updated_at`, `capacity`, `year_level`, `user_id`, `program_id`) VALUES
(2, 'CS-2-A', '2024-08-14 07:02:07', '2024-09-09 07:45:12', 0, '2nd Year', 19, 1),
(3, 'IT-2-A', '2024-08-14 07:02:07', '2024-09-09 07:45:20', 0, '2nd Year', 19, 2),
(4, 'Section A-BSA', '2024-08-28 09:09:07', '2024-09-08 06:07:08', 0, '0', 26, NULL),
(10, 'son-4-c', '2024-09-10 13:41:22', '2024-09-10 13:41:22', 20, '1st Year', 27, 17);

-- --------------------------------------------------------

--
-- Table structure for table `section_courses`
--

CREATE TABLE `section_courses` (
  `section_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `section_courses`
--

INSERT INTO `section_courses` (`section_id`, `course_id`) VALUES
(2, 21),
(2, 22),
(2, 23),
(2, 24),
(2, 25),
(2, 28),
(3, 26),
(3, 27),
(3, 29),
(3, 30),
(3, 31),
(4, 32),
(4, 33),
(4, 34),
(10, 51),
(10, 52);

-- --------------------------------------------------------

--
-- Table structure for table `unavailable_times`
--

CREATE TABLE `unavailable_times` (
  `id` int(11) NOT NULL,
  `section_id` int(11) NOT NULL,
  `day_of_week` enum('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday') COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_time` decimal(50,2) NOT NULL,
  `end_time` decimal(50,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `unavailable_times`
--

INSERT INTO `unavailable_times` (`id`, `section_id`, `day_of_week`, `start_time`, `end_time`) VALUES
(18, 2, 'Monday', '8.50', '10.00'),
(19, 2, 'Wednesday', '8.50', '10.00'),
(20, 2, 'Monday', '10.00', '11.50'),
(21, 2, 'Wednesday', '10.00', '11.50'),
(22, 2, 'Tuesday', '16.00', '17.50'),
(23, 2, 'Friday', '16.00', '17.50'),
(26, 3, 'Tuesday', '7.00', '8.50'),
(27, 3, 'Friday', '7.00', '8.50'),
(28, 3, 'Tuesday', '16.00', '17.50'),
(29, 3, 'Friday', '16.00', '17.50'),
(30, 3, 'Thursday', '13.00', '16.00'),
(31, 3, 'Monday', '15.00', '16.50'),
(32, 3, 'Wednesday', '15.00', '16.50'),
(33, 4, 'Monday', '17.50', '20.50'),
(34, 2, 'Thursday', '7.00', '20.00'),
(45, 10, 'Monday', '7.50', '8.50');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `username` varchar(100) NOT NULL,
  `email` varchar(200) NOT NULL,
  `role` enum('gen-ed','registrar','dept-head','admin') NOT NULL,
  `department` enum('CSIT','ENGINEERING','SON','SBMA','SHOM','SEAS','REGISTRAR','ADMIN','GENED') NOT NULL,
  `password` varchar(200) NOT NULL,
  `is_verified` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `username`, `email`, `role`, `department`, `password`, `is_verified`) VALUES
(19, 'asd', '123@gmail.com', 'dept-head', 'CSIT', '$2b$12$v4u3G2W/mCM.Da.HzJpWve5PxnulCs69MffDjxE5n4w9OC.8UICDm', 1),
(21, 'admin1', 'admin@gmail.com', 'admin', 'ADMIN', '$2b$12$AWe8tDr/KXM1HR0hecg8F.WPT92ugZ7rXwS41IXVJQYZfDQ.80m4W', 1),
(22, 'registrar', 'registrar@gmail.com', 'registrar', 'REGISTRAR', '$2b$12$ifjIP5Ceg6o7mH.rLpjKwujzkhnhLCoxlik5blvxyD7xiCxyQ6EQK', 1),
(23, 'seas', 'seas@gmail.com', 'dept-head', 'SEAS', '$2b$12$mzbySaSlcewM0xXwcvjMDOWyJ3jXfzM1YROeJj2xmaOR21OEh178.', 1),
(26, 'daria', 'ma.darialabalan@gmail.com', 'dept-head', 'SBMA', '$2b$12$9uWQ4ouxVMTtdUPpMhPufuXtyX9bsMRrBJG/.4YJSmZKjGRzM4qF2', 0),
(27, 'fatima', 'fatimabalbin@gmail.com', 'dept-head', 'SON', '$2b$12$WSZOQwanyfh/qa588C7RKe.AGpLxDmpTegl8w66npto3FKN.hYsqi', 1),
(29, 'gened', 'gened@gmail.com', 'gen-ed', 'GENED', '$2b$12$MDHdh5PfBI3qY2VMtV46c.UTUUIXxy02wJc3NrAPtPfw6oyC88.i.', 0);

-- --------------------------------------------------------

--
-- Table structure for table `user_solutions`
--

CREATE TABLE `user_solutions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `section_id` int(11) DEFAULT NULL,
  `course_id` int(11) DEFAULT NULL,
  `day` varchar(10) DEFAULT NULL,
  `start_hour` decimal(4,2) DEFAULT NULL,
  `duration` decimal(4,2) DEFAULT NULL,
  `course_code` varchar(10) DEFAULT NULL,
  `course_block` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `user_solutions`
--

INSERT INTO `user_solutions` (`id`, `user_id`, `section_id`, `course_id`, `day`, `start_hour`, `duration`, `course_code`, `course_block`) VALUES
(2774, 19, 2, -1, 'Monday', '8.50', '1.50', 'Unavailabl', 'None'),
(2775, 19, 2, -1, 'Wednesday', '8.50', '1.50', 'Unavailabl', 'None'),
(2776, 19, 2, -1, 'Monday', '10.00', '1.50', 'Unavailabl', 'None'),
(2777, 19, 2, -1, 'Wednesday', '10.00', '1.50', 'Unavailabl', 'None'),
(2778, 19, 2, -1, 'Tuesday', '16.00', '1.50', 'Unavailabl', 'None'),
(2779, 19, 2, -1, 'Friday', '16.00', '1.50', 'Unavailabl', 'None'),
(2780, 19, 2, -1, 'Thursday', '13.00', '7.00', 'Unavailabl', 'None'),
(2781, 19, 2, 21, 'Thursday', '17.50', '2.50', 'CC103', 'A'),
(2782, 19, 2, 21, 'Saturday', '17.50', '2.50', 'CC103', 'A'),
(2783, 19, 2, 22, 'Thursday', '10.00', '1.50', 'CS PC 211', 'A'),
(2784, 19, 2, 22, 'Saturday', '10.00', '1.50', 'CS PC 211', 'A'),
(2785, 19, 2, 24, 'Thursday', '14.00', '1.50', 'CS PC ELEC', 'A'),
(2786, 19, 2, 24, 'Saturday', '14.00', '1.50', 'CS PC ELEC', 'A'),
(2787, 19, 2, 25, 'Tuesday', '10.00', '1.50', 'MATH 100', 'A'),
(2788, 19, 2, 25, 'Friday', '10.00', '1.50', 'MATH 100', 'A'),
(2789, 19, 2, 28, 'Monday', '15.00', '1.00', 'IT PC 212', 'A'),
(2790, 19, 2, 23, 'Tuesday', '8.00', '1.50', 'CS PC 212', 'A'),
(2791, 19, 2, 23, 'Friday', '8.00', '1.50', 'CS PC 212', 'A'),
(2792, 19, 3, -1, 'Tuesday', '7.00', '1.50', 'Unavailabl', 'None'),
(2793, 19, 3, -1, 'Friday', '7.00', '1.50', 'Unavailabl', 'None'),
(2794, 19, 3, -1, 'Tuesday', '16.00', '1.50', 'Unavailabl', 'None'),
(2795, 19, 3, -1, 'Friday', '16.00', '1.50', 'Unavailabl', 'None'),
(2796, 19, 3, -1, 'Thursday', '13.00', '3.00', 'Unavailabl', 'None'),
(2797, 19, 3, -1, 'Monday', '15.00', '1.50', 'Unavailabl', 'None'),
(2798, 19, 3, -1, 'Wednesday', '15.00', '1.50', 'Unavailabl', 'None'),
(2799, 19, 3, 26, 'Thursday', '17.50', '2.50', 'CC103', 'A'),
(2800, 19, 3, 26, 'Saturday', '17.50', '2.50', 'CC103', 'A'),
(2801, 19, 3, 29, 'Monday', '15.00', '1.00', 'IT PC 212', 'A'),
(2802, 19, 3, 27, 'Thursday', '16.00', '1.50', 'IT ELEC 01', 'A'),
(2803, 19, 3, 27, 'Saturday', '16.00', '1.50', 'IT ELEC 01', 'A'),
(2804, 19, 3, 30, 'Monday', '8.00', '1.50', 'IT PC 213', 'A'),
(2805, 19, 3, 30, 'Wednesday', '8.00', '1.50', 'IT PC 213', 'A'),
(2806, 19, 3, 31, 'Thursday', '9.00', '1.50', 'IT PC 211', 'A'),
(2807, 19, 3, 31, 'Saturday', '9.00', '1.50', 'IT PC 211', 'A'),
(2808, 27, 10, -1, 'Monday', '7.00', '1.50', 'Unavailabl', 'None'),
(2809, 27, 10, 51, 'Thursday', '17.00', '2.00', 'nursing1', 'A'),
(2810, 27, 10, 51, 'Saturday', '17.00', '2.00', 'nursing1', 'A'),
(2811, 27, 10, 52, 'Tuesday', '9.00', '2.50', 'nursing2', 'A'),
(2812, 27, 10, 52, 'Friday', '9.00', '2.50', 'nursing2', 'A'),
(2813, 27, 10, 53, 'Tuesday', '16.00', '2.50', 'nursing3', 'A'),
(2814, 27, 10, 53, 'Friday', '16.00', '2.50', 'nursing3', 'A');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `allocations`
--
ALTER TABLE `allocations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `course_id` (`course_id`),
  ADD KEY `room_id` (`room_id`);

--
-- Indexes for table `classrooms`
--
ALTER TABLE `classrooms`
  ADD PRIMARY KEY (`room_id`);

--
-- Indexes for table `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`course_id`),
  ADD KEY `program_id` (`program_id`),
  ADD KEY `faculty_id` (`faculty_id`);

--
-- Indexes for table `created_schedules`
--
ALTER TABLE `created_schedules`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `faculties`
--
ALTER TABLE `faculties`
  ADD PRIMARY KEY (`faculty_id`);

--
-- Indexes for table `gened_courses`
--
ALTER TABLE `gened_courses`
  ADD PRIMARY KEY (`course_id`),
  ADD KEY `faculty_id` (`faculty_id`);

--
-- Indexes for table `gened_solutions`
--
ALTER TABLE `gened_solutions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_gened_solutions_users` (`user_id`),
  ADD KEY `fk_gened_solutions_gened_courses` (`course_id`);

--
-- Indexes for table `programs`
--
ALTER TABLE `programs`
  ADD PRIMARY KEY (`program_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `room_courses`
--
ALTER TABLE `room_courses`
  ADD PRIMARY KEY (`course_id`);

--
-- Indexes for table `sections`
--
ALTER TABLE `sections`
  ADD PRIMARY KEY (`section_id`),
  ADD KEY `fk_user_section` (`user_id`),
  ADD KEY `fk_sections_programs` (`program_id`);

--
-- Indexes for table `section_courses`
--
ALTER TABLE `section_courses`
  ADD PRIMARY KEY (`section_id`,`course_id`),
  ADD KEY `course_id` (`course_id`);

--
-- Indexes for table `unavailable_times`
--
ALTER TABLE `unavailable_times`
  ADD PRIMARY KEY (`id`),
  ADD KEY `section_id` (`section_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`);

--
-- Indexes for table `user_solutions`
--
ALTER TABLE `user_solutions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `allocations`
--
ALTER TABLE `allocations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `classrooms`
--
ALTER TABLE `classrooms`
  MODIFY `room_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `courses`
--
ALTER TABLE `courses`
  MODIFY `course_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=54;

--
-- AUTO_INCREMENT for table `created_schedules`
--
ALTER TABLE `created_schedules`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=145;

--
-- AUTO_INCREMENT for table `faculties`
--
ALTER TABLE `faculties`
  MODIFY `faculty_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=35;

--
-- AUTO_INCREMENT for table `gened_courses`
--
ALTER TABLE `gened_courses`
  MODIFY `course_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- AUTO_INCREMENT for table `gened_solutions`
--
ALTER TABLE `gened_solutions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=335;

--
-- AUTO_INCREMENT for table `programs`
--
ALTER TABLE `programs`
  MODIFY `program_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT for table `room_courses`
--
ALTER TABLE `room_courses`
  MODIFY `course_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sections`
--
ALTER TABLE `sections`
  MODIFY `section_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `unavailable_times`
--
ALTER TABLE `unavailable_times`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=46;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=30;

--
-- AUTO_INCREMENT for table `user_solutions`
--
ALTER TABLE `user_solutions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2815;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `allocations`
--
ALTER TABLE `allocations`
  ADD CONSTRAINT `allocations_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `room_courses` (`course_id`),
  ADD CONSTRAINT `allocations_ibfk_2` FOREIGN KEY (`room_id`) REFERENCES `classrooms` (`room_id`);

--
-- Constraints for table `courses`
--
ALTER TABLE `courses`
  ADD CONSTRAINT `courses_ibfk_1` FOREIGN KEY (`program_id`) REFERENCES `programs` (`program_id`),
  ADD CONSTRAINT `courses_ibfk_2` FOREIGN KEY (`faculty_id`) REFERENCES `faculties` (`faculty_id`);

--
-- Constraints for table `created_schedules`
--
ALTER TABLE `created_schedules`
  ADD CONSTRAINT `created_schedules_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `gened_courses`
--
ALTER TABLE `gened_courses`
  ADD CONSTRAINT `gened_courses_ibfk_1` FOREIGN KEY (`faculty_id`) REFERENCES `faculties` (`faculty_id`);

--
-- Constraints for table `gened_solutions`
--
ALTER TABLE `gened_solutions`
  ADD CONSTRAINT `fk_gened_solutions_gened_courses` FOREIGN KEY (`course_id`) REFERENCES `gened_courses` (`course_id`),
  ADD CONSTRAINT `fk_gened_solutions_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  ADD CONSTRAINT `gened_solutions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `programs`
--
ALTER TABLE `programs`
  ADD CONSTRAINT `programs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `sections`
--
ALTER TABLE `sections`
  ADD CONSTRAINT `fk_sections_programs` FOREIGN KEY (`program_id`) REFERENCES `programs` (`program_id`),
  ADD CONSTRAINT `fk_user_section` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `section_courses`
--
ALTER TABLE `section_courses`
  ADD CONSTRAINT `section_courses_ibfk_1` FOREIGN KEY (`section_id`) REFERENCES `sections` (`section_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `section_courses_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE;

--
-- Constraints for table `unavailable_times`
--
ALTER TABLE `unavailable_times`
  ADD CONSTRAINT `unavailable_times_ibfk_1` FOREIGN KEY (`section_id`) REFERENCES `sections` (`section_id`);

--
-- Constraints for table `user_solutions`
--
ALTER TABLE `user_solutions`
  ADD CONSTRAINT `user_solutions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
