-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Sep 28, 2024 at 11:38 AM
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

--
-- Dumping data for table `allocations`
--

INSERT INTO `allocations` (`id`, `course_id`, `room_id`) VALUES
(725, 279, 22),
(726, 280, 22),
(727, 281, 19),
(728, 282, 19),
(729, 283, 18),
(730, 284, 18),
(731, 285, 18),
(732, 286, 18),
(733, 287, 20),
(734, 288, 20),
(735, 289, 20),
(736, 290, 20),
(737, 291, 19),
(738, 292, 19),
(739, 293, 19),
(740, 294, 19),
(741, 295, 21),
(742, 296, 21),
(743, 297, 22),
(744, 298, 22),
(745, 299, 18),
(746, 300, 18),
(747, 301, 18),
(748, 302, 18),
(749, 303, 21),
(750, 304, 24),
(751, 305, 24),
(752, 306, 24),
(753, 307, 24),
(754, 308, 26),
(755, 309, 26),
(756, 310, 28),
(757, 311, 28),
(758, 312, 19),
(759, 313, 19),
(760, 314, 24),
(761, 315, 28),
(762, 316, 28),
(763, 317, 23),
(764, 318, 23),
(765, 319, 27),
(766, 320, 27);

-- --------------------------------------------------------

--
-- Table structure for table `classrooms`
--

CREATE TABLE `classrooms` (
  `room_id` int(11) NOT NULL,
  `room_no` varchar(255) NOT NULL,
  `capacity` int(200) NOT NULL,
  `type` varchar(100) NOT NULL,
  `floor_level` int(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `classrooms`
--

INSERT INTO `classrooms` (`room_id`, `room_no`, `capacity`, `type`, `floor_level`) VALUES
(18, '1', 40, 'Lecture', 1),
(19, '2', 40, 'Lecture', 1),
(20, '3', 40, 'Lecture', 1),
(21, '4', 40, 'Lecture', 1),
(22, '5', 30, 'Lecture', 2),
(23, '115', 30, 'Networking', 4),
(24, '116', 50, 'Lecture', 4),
(25, '117A', 30, 'Comp Laboratory', 4),
(26, '117B', 30, 'Comp Laboratory', 4),
(27, '118', 40, 'Comp Laboratory', 4),
(28, '119', 30, 'Comp Laboratory', 4);

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
(54, 'CC103', 'DATA STRUCTURES AND ALGORITHMS', 'A', 'Lecture', '2nd Year', '3.00', '5.00', 21, 39),
(55, 'CC103', 'DATA STRUCTURES AND ALGORITHMS', 'A', 'Lecture', '2nd Year', '3.00', '5.00', 20, 39),
(56, 'CS PC 211', 'DISCRETE STRUCTURES 2', 'A', 'Lecture', '2nd Year', '3.00', '5.00', 20, 40),
(57, 'CS PC 212', 'OBJECT ORIENTED PROGRAMMING', 'A', 'Comp Laboratory', '2nd Year', '3.00', '5.00', 20, 39),
(58, 'CS PC ELEC 01', 'FUNDAMENTALS OF HUMAN COMPUTER INTERACTION', 'A', 'Comp Laboratory', '2nd Year', '3.00', '5.00', 20, 41),
(59, 'MATH 100', 'CALCULUS', 'A', 'Lecture', '2nd Year', '3.00', '3.00', 20, 44),
(60, 'IT PC 212', 'RELATED LEARNING EXPERIENCE', 'A', 'Lecture', '2nd Year', '1.00', '1.00', 20, 39),
(61, 'IT ELEC 01', 'IT ELECTIVE 1', 'A', 'Comp Laboratory', '2nd Year', '3.00', '5.00', 21, 42),
(62, 'IT PC 212', 'RELATED LEARNING EXPERIENCE', 'A', 'Lecture', '2nd Year', '1.00', '1.00', 21, 39),
(63, 'IT PC 213', 'NETWORKING 1', 'A', 'Networking', '2nd Year', '3.00', '3.00', 21, 43),
(64, 'IT PC 211', 'INTRODUCTION TO HUMAN COMPUTER INTERACTION', 'A', 'Comp Laboratory', '2nd Year', '3.00', '3.00', 21, 44),
(67, 'CC100', 'Intro to computing', 'A', 'Comp Laboratory', '1st Year', '3.00', '5.00', 21, 42),
(68, 'CC101', 'Comprog 1', 'A', 'Comp Laboratory', '1st Year', '3.00', '5.00', 21, 41);

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
-- Table structure for table `created_gened_schedules`
--

CREATE TABLE `created_gened_schedules` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `course_id` int(11) DEFAULT NULL,
  `day` varchar(10) DEFAULT NULL,
  `start_hour` decimal(4,2) DEFAULT NULL,
  `duration` decimal(4,2) DEFAULT NULL,
  `course_code` varchar(10) DEFAULT NULL,
  `course_block` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `created_gened_schedules`
--

INSERT INTO `created_gened_schedules` (`id`, `user_id`, `course_id`, `day`, `start_hour`, `duration`, `course_code`, `course_block`) VALUES
(121, 30, 17, 'Tuesday', '13.00', '1.50', 'GE 01', 'A'),
(122, 30, 17, 'Wednesday', '13.00', '1.50', 'GE 01', 'A'),
(123, 30, 18, 'Thursday', '11.50', '1.50', 'GE 01', 'B'),
(124, 30, 18, 'Saturday', '11.50', '1.50', 'GE 01', 'B'),
(125, 30, 19, 'Monday', '11.00', '1.00', 'GE 01', 'C'),
(126, 30, 19, 'Wednesday', '11.00', '1.00', 'GE 01', 'C'),
(127, 30, 20, 'Monday', '7.00', '1.50', 'GE 04', 'A'),
(128, 30, 20, 'Wednesday', '7.00', '1.50', 'GE 04', 'A'),
(129, 30, 21, 'Tuesday', '16.00', '1.50', 'GE 04', 'B'),
(130, 30, 21, 'Friday', '16.00', '1.50', 'GE 04', 'B'),
(131, 30, 22, 'Thursday', '14.00', '1.50', 'GE 04', 'C'),
(132, 30, 22, 'Saturday', '14.00', '1.50', 'GE 04', 'C'),
(133, 30, 23, 'Thursday', '9.00', '1.50', 'GE 05', 'A'),
(134, 30, 23, 'Saturday', '9.00', '1.50', 'GE 05', 'A'),
(135, 30, 24, 'Monday', '7.00', '1.50', 'GE 05', 'B'),
(136, 30, 24, 'Wednesday', '7.00', '1.50', 'GE 05', 'B'),
(137, 30, 25, 'Tuesday', '11.00', '1.00', 'GE 05', 'C'),
(138, 30, 25, 'Friday', '11.00', '1.00', 'GE 05', 'C'),
(139, 30, 26, 'Tuesday', '8.00', '1.50', 'GE 07', 'A'),
(140, 30, 26, 'Friday', '8.00', '1.50', 'GE 07', 'A'),
(141, 30, 27, 'Tuesday', '16.00', '1.50', 'GE 07', 'B'),
(142, 30, 27, 'Friday', '16.00', '1.50', 'GE 07', 'B'),
(143, 30, 28, 'Tuesday', '13.00', '1.50', 'GE 07', 'C'),
(144, 30, 28, 'Friday', '13.00', '1.50', 'GE 07', 'C'),
(145, 30, 30, 'Thursday', '13.00', '1.00', 'try1', 'A');

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
(35, 'understanding', 'teacher', 'Full Time', '30.00', 'GENED', 24.01),
(36, 'math', 'teacher', 'Full Time', '25.00', 'GENED', 10),
(37, 'communicating', 'teacher', 'Full Time', '25.00', 'GENED', 9),
(38, 'science', 'teacher', 'Full Time', '25.00', 'GENED', 9),
(39, 'Mary Grace', 'Enriquez', 'Full Time', '25.00', 'CSIT', 11.001),
(40, 'Rhodora Faye', 'Brosas', 'Full Time', '25.00', 'CSIT', 3),
(41, 'Relian', 'Cadubla', 'Full Time', '25.00', 'CSIT', 6),
(42, 'Jp', 'Serrano', 'Full Time', '25.00', 'CSIT', 6),
(43, 'Jay', ' Benaraba', 'Full Time', '25.00', 'CSIT', 3),
(44, 'Shaira', 'Pepeno', 'Full Time', '25.00', 'CSIT', 6),
(45, 'Rizal', 'Teacher', 'Full Time', '25.00', 'GENED', 0);

-- --------------------------------------------------------

--
-- Table structure for table `final_allocations`
--

CREATE TABLE `final_allocations` (
  `id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL,
  `room_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `final_allocations`
--

INSERT INTO `final_allocations` (`id`, `course_id`, `room_id`) VALUES
(186, 279, 22),
(187, 280, 22),
(188, 281, 19),
(189, 282, 19),
(190, 283, 18),
(191, 284, 18),
(192, 285, 18),
(193, 286, 18),
(194, 287, 20),
(195, 288, 20),
(196, 289, 20),
(197, 290, 20),
(198, 291, 19),
(199, 292, 19),
(200, 293, 19),
(201, 294, 19),
(202, 295, 21),
(203, 296, 21),
(204, 297, 22),
(205, 298, 22),
(206, 299, 18),
(207, 300, 18),
(208, 301, 18),
(209, 302, 18),
(210, 303, 21),
(211, 304, 24),
(212, 305, 24),
(213, 306, 24),
(214, 307, 24),
(215, 308, 26),
(216, 309, 26),
(217, 310, 28),
(218, 311, 28),
(219, 312, 19),
(220, 313, 19),
(221, 314, 24),
(222, 315, 28),
(223, 316, 28),
(224, 317, 23),
(225, 318, 23),
(226, 319, 27),
(227, 320, 27);

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
  `faculty_id` int(11) DEFAULT NULL,
  `capacity` int(11) NOT NULL,
  `type` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `gened_courses`
--

INSERT INTO `gened_courses` (`course_id`, `course_code`, `course_name`, `course_block`, `units`, `hours_per_week`, `faculty_id`, `capacity`, `type`) VALUES
(17, 'GE 01', 'UNDERSTANDING THE SELF', 'A', '3.00', '3.00', 35, 30, 'Lecture'),
(18, 'GE 01', 'UNDERSTANDING THE SELF', 'B', '3.00', '3.00', 35, 30, 'Lecture'),
(19, 'GE 01', 'UNDERSTANDING THE SELF', 'C', '3.00', '3.00', 35, 30, 'Lecture'),
(20, 'GE 04', 'MATHEMATICS IN THE MODERN WORLD', 'A', '3.00', '3.00', 36, 30, 'Lecture'),
(21, 'GE 04', 'MATHEMATICS IN THE MODERN WORLD', 'B', '3.00', '3.00', 36, 30, 'Lecture'),
(22, 'GE 04', 'MATHEMATICS IN THE MODERN WORLD', 'C', '3.00', '3.00', 36, 30, 'Lecture'),
(23, 'GE 05', 'PURPOSIVE COMMUNICATION', 'A', '3.00', '3.00', 37, 30, 'Lecture'),
(24, 'GE 05', 'PURPOSIVE COMMUNICATION', 'B', '3.00', '3.00', 37, 30, 'Lecture'),
(25, 'GE 05', 'PURPOSIVE COMMUNICATION', 'C', '3.00', '3.00', 37, 30, 'Lecture'),
(26, 'GE 07', 'SCIENCE, TECHNOLOGY AND SOCIETY', 'A', '3.00', '3.00', 38, 30, 'Lecture'),
(27, 'GE 07', 'SCIENCE, TECHNOLOGY AND SOCIETY', 'B', '3.00', '3.00', 38, 30, 'Lecture'),
(28, 'GE 07', 'SCIENCE, TECHNOLOGY AND SOCIETY', 'C', '3.00', '3.00', 38, 30, 'Lecture'),
(30, 'try1', 'try1', 'A', '1.00', '1.00', 36, 30, 'Lecture'),
(31, 'Ge 01', 'UNDERSTANDING THE SELF', 'D', '3.00', '3.00', 35, 30, 'Lecture');

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
(874, 30, 17, 'Thursday', '15.00', '1.50', 'GE 01', 'A'),
(875, 30, 17, 'Saturday', '15.00', '1.50', 'GE 01', 'A'),
(876, 30, 18, 'Monday', '9.00', '1.50', 'GE 01', 'B'),
(877, 30, 18, 'Wednesday', '9.00', '1.50', 'GE 01', 'B'),
(878, 30, 19, 'Tuesday', '15.00', '1.50', 'GE 01', 'C'),
(879, 30, 19, 'Friday', '15.00', '1.50', 'GE 01', 'C'),
(880, 30, 20, 'Monday', '11.00', '1.00', 'GE 04', 'A'),
(881, 30, 20, 'Wednesday', '11.00', '1.00', 'GE 04', 'A'),
(882, 30, 21, 'Monday', '7.00', '1.50', 'GE 04', 'B'),
(883, 30, 21, 'Wednesday', '7.00', '1.50', 'GE 04', 'B'),
(884, 30, 22, 'Monday', '9.00', '1.50', 'GE 04', 'C'),
(885, 30, 22, 'Wednesday', '9.00', '1.50', 'GE 04', 'C'),
(886, 30, 23, 'Tuesday', '15.00', '1.50', 'GE 05', 'A'),
(887, 30, 23, 'Friday', '15.00', '1.50', 'GE 05', 'A'),
(888, 30, 24, 'Tuesday', '9.00', '1.50', 'GE 05', 'B'),
(889, 30, 24, 'Friday', '9.00', '1.50', 'GE 05', 'B'),
(890, 30, 25, 'Monday', '15.00', '1.50', 'GE 05', 'C'),
(891, 30, 25, 'Wednesday', '15.00', '1.50', 'GE 05', 'C'),
(892, 30, 26, 'Thursday', '16.00', '1.50', 'GE 07', 'A'),
(893, 30, 26, 'Saturday', '16.00', '1.50', 'GE 07', 'A'),
(894, 30, 27, 'Monday', '10.00', '1.50', 'GE 07', 'B'),
(895, 30, 27, 'Wednesday', '10.00', '1.50', 'GE 07', 'B'),
(896, 30, 28, 'Thursday', '7.00', '1.50', 'GE 07', 'C'),
(897, 30, 28, 'Saturday', '7.00', '1.50', 'GE 07', 'C'),
(898, 30, 30, 'Friday', '13.00', '1.00', 'try1', 'A'),
(899, 30, 31, 'Thursday', '8.00', '1.50', 'Ge 01', 'D'),
(900, 30, 31, 'Saturday', '8.00', '1.50', 'Ge 01', 'D');

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
(20, 'BSCS', 32),
(21, 'BSIT', 32);

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

--
-- Dumping data for table `room_courses`
--

INSERT INTO `room_courses` (`course_id`, `course_code`, `capacity`, `type`, `block`, `department`, `start_time`, `end_time`, `day`) VALUES
(279, 'GE 01', 30, 'Lecture', 'A', 'GENED', '13.00', '14.50', 'Tuesday'),
(280, 'GE 01', 30, 'Lecture', 'A', 'GENED', '13.00', '14.50', 'Wednesday'),
(281, 'GE 01', 30, 'Lecture', 'B', 'GENED', '11.50', '13.00', 'Thursday'),
(282, 'GE 01', 30, 'Lecture', 'B', 'GENED', '11.50', '13.00', 'Saturday'),
(283, 'GE 01', 30, 'Lecture', 'C', 'GENED', '11.00', '12.00', 'Monday'),
(284, 'GE 01', 30, 'Lecture', 'C', 'GENED', '11.00', '12.00', 'Wednesday'),
(285, 'GE 04', 30, 'Lecture', 'A', 'GENED', '7.00', '8.50', 'Monday'),
(286, 'GE 04', 30, 'Lecture', 'A', 'GENED', '7.00', '8.50', 'Wednesday'),
(287, 'GE 04', 30, 'Lecture', 'B', 'GENED', '16.00', '17.50', 'Tuesday'),
(288, 'GE 04', 30, 'Lecture', 'B', 'GENED', '16.00', '17.50', 'Friday'),
(289, 'GE 04', 30, 'Lecture', 'C', 'GENED', '14.00', '15.50', 'Thursday'),
(290, 'GE 04', 30, 'Lecture', 'C', 'GENED', '14.00', '15.50', 'Saturday'),
(291, 'GE 05', 30, 'Lecture', 'A', 'GENED', '9.00', '10.50', 'Thursday'),
(292, 'GE 05', 30, 'Lecture', 'A', 'GENED', '9.00', '10.50', 'Saturday'),
(293, 'GE 05', 30, 'Lecture', 'B', 'GENED', '7.00', '8.50', 'Monday'),
(294, 'GE 05', 30, 'Lecture', 'B', 'GENED', '7.00', '8.50', 'Wednesday'),
(295, 'GE 05', 30, 'Lecture', 'C', 'GENED', '11.00', '12.00', 'Tuesday'),
(296, 'GE 05', 30, 'Lecture', 'C', 'GENED', '11.00', '12.00', 'Friday'),
(297, 'GE 07', 30, 'Lecture', 'A', 'GENED', '8.00', '9.50', 'Tuesday'),
(298, 'GE 07', 30, 'Lecture', 'A', 'GENED', '8.00', '9.50', 'Friday'),
(299, 'GE 07', 30, 'Lecture', 'B', 'GENED', '16.00', '17.50', 'Tuesday'),
(300, 'GE 07', 30, 'Lecture', 'B', 'GENED', '16.00', '17.50', 'Friday'),
(301, 'GE 07', 30, 'Lecture', 'C', 'GENED', '13.00', '14.50', 'Tuesday'),
(302, 'GE 07', 30, 'Lecture', 'C', 'GENED', '13.00', '14.50', 'Friday'),
(303, 'try1', 30, 'Lecture', 'A', 'GENED', '13.00', '14.00', 'Thursday'),
(304, 'CC103', 10, 'Lecture', 'A', 'CSIT', '10.00', '12.00', 'Tuesday'),
(305, 'CC103', 10, 'Lecture', 'A', 'CSIT', '10.00', '12.00', 'Friday'),
(306, 'CS PC 211', 10, 'Lecture', 'A', 'CSIT', '15.00', '17.50', 'Tuesday'),
(307, 'CS PC 211', 10, 'Lecture', 'A', 'CSIT', '15.00', '17.50', 'Friday'),
(308, 'CS PC 212', 10, 'Comp Laboratory', 'A', 'CSIT', '16.00', '18.50', 'Thursday'),
(309, 'CS PC 212', 10, 'Comp Laboratory', 'A', 'CSIT', '16.00', '18.50', 'Saturday'),
(310, 'CS PC ELEC', 10, 'Comp Laboratory', 'A', 'CSIT', '10.00', '12.00', 'Thursday'),
(311, 'CS PC ELEC', 10, 'Comp Laboratory', 'A', 'CSIT', '10.00', '12.00', 'Saturday'),
(312, 'MATH 100', 10, 'Lecture', 'A', 'CSIT', '14.00', '15.50', 'Thursday'),
(313, 'MATH 100', 10, 'Lecture', 'A', 'CSIT', '14.00', '15.50', 'Saturday'),
(314, 'IT PC 212', 10, 'Lecture', 'A', 'CSIT', '13.00', '14.00', 'Monday'),
(315, 'IT ELEC 01', 30, 'Comp Laboratory', 'A', 'CSIT', '14.00', '16.50', 'Monday'),
(316, 'IT ELEC 01', 30, 'Comp Laboratory', 'A', 'CSIT', '14.00', '16.50', 'Wednesday'),
(317, 'IT PC 213', 30, 'Networking', 'A', 'CSIT', '9.00', '10.50', 'Thursday'),
(318, 'IT PC 213', 30, 'Networking', 'A', 'CSIT', '9.00', '10.50', 'Saturday'),
(319, 'IT PC 211', 30, 'Comp Laboratory', 'A', 'CSIT', '18.00', '19.50', 'Tuesday'),
(320, 'IT PC 211', 30, 'Comp Laboratory', 'A', 'CSIT', '18.00', '19.50', 'Friday');

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
(11, 'CS-2-A', '2024-09-22 07:46:19', '2024-09-22 07:46:19', 10, '2nd Year', 32, 20),
(12, 'IT-2-A', '2024-09-22 07:46:45', '2024-09-22 07:46:45', 30, '2nd Year', 32, 21),
(13, 'It-1-A', '2024-09-26 09:31:50', '2024-09-26 09:31:50', 30, '1st Year', 32, 21);

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
(11, 55),
(11, 56),
(11, 57),
(11, 58),
(11, 59),
(11, 60),
(12, 54),
(12, 61),
(12, 62),
(12, 63),
(12, 64),
(13, 67),
(13, 68);

-- --------------------------------------------------------

--
-- Table structure for table `unavailable_times`
--

CREATE TABLE `unavailable_times` (
  `id` int(11) NOT NULL,
  `course_code` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `block` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `section_id` int(11) NOT NULL,
  `day_of_week` enum('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday') COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_time` decimal(50,2) NOT NULL,
  `end_time` decimal(50,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `unavailable_times`
--

INSERT INTO `unavailable_times` (`id`, `course_code`, `block`, `section_id`, `day_of_week`, `start_time`, `end_time`) VALUES
(53, 'GE 04', 'A', 11, 'Monday', '7.00', '8.50'),
(54, 'GE 04', 'A', 11, 'Wednesday', '7.00', '8.50');

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
(21, 'admin', 'admin@gmail.com', 'admin', 'ADMIN', '$2b$12$AWe8tDr/KXM1HR0hecg8F.WPT92ugZ7rXwS41IXVJQYZfDQ.80m4W', 1),
(30, 'gened1', 'gened@gmail.com', 'gen-ed', 'GENED', '$2b$12$PxhfwQZl.p5hQ/h.48alZ.ChM7lSajVicRIprGXbr/auLeDrX6zdy', 1),
(31, 'registrar', 'registrar@gmail.com', 'registrar', 'REGISTRAR', '$2b$12$PxhfwQZl.p5hQ/h.48alZ.ChM7lSajVicRIprGXbr/auLeDrX6zdy', 1),
(32, 'csit', 'csit@gmail.com', 'dept-head', 'CSIT', '$2b$12$PxhfwQZl.p5hQ/h.48alZ.ChM7lSajVicRIprGXbr/auLeDrX6zdy', 1),
(33, 'son', 'son@gmail.com', 'dept-head', 'SON', '$2b$12$PxhfwQZl.p5hQ/h.48alZ.ChM7lSajVicRIprGXbr/auLeDrX6zdy', 1),
(38, 'seas', 'seas@gmail.com', 'dept-head', 'SEAS', '$2b$12$nI9F9r74eQ3OtZ.2DTfjee1CmBTMz5Ofr0kbrBMs8NOjZVORsb50C', 1),
(39, 'shom', 'shom@gmail.com', 'dept-head', 'SHOM', '$2b$12$Tp1uYYlYdYzxaGPjJg6bFen8drHd3A8RpgdOzWFkGDwclk6HTrGGG', 0);

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
(4737, 32, 11, -1, 'Monday', '7.00', '1.50', 'GE 04', 'A'),
(4738, 32, 11, -1, 'Wednesday', '7.00', '1.50', 'GE 04', 'A'),
(4739, 32, 11, 55, 'Monday', '10.00', '2.00', 'CC103', 'A'),
(4740, 32, 11, 55, 'Wednesday', '10.00', '2.00', 'CC103', 'A'),
(4741, 32, 11, 56, 'Thursday', '15.00', '2.50', 'CS PC 211', 'A'),
(4742, 32, 11, 56, 'Saturday', '15.00', '2.50', 'CS PC 211', 'A'),
(4743, 32, 11, 57, 'Thursday', '8.00', '2.50', 'CS PC 212', 'A'),
(4744, 32, 11, 57, 'Saturday', '8.00', '2.50', 'CS PC 212', 'A'),
(4745, 32, 11, 58, 'Monday', '17.00', '2.50', 'CS PC ELEC', 'A'),
(4746, 32, 11, 58, 'Wednesday', '17.00', '2.50', 'CS PC ELEC', 'A'),
(4747, 32, 11, 59, 'Tuesday', '13.00', '1.50', 'MATH 100', 'A'),
(4748, 32, 11, 59, 'Friday', '13.00', '1.50', 'MATH 100', 'A'),
(4749, 32, 11, 60, 'Tuesday', '10.00', '1.00', 'IT PC 212', 'A'),
(4750, 32, 12, 54, 'Monday', '10.00', '2.00', 'CC103', 'A'),
(4751, 32, 12, 54, 'Wednesday', '10.00', '2.00', 'CC103', 'A'),
(4752, 32, 12, 62, 'Tuesday', '10.00', '1.00', 'IT PC 212', 'A'),
(4753, 32, 12, 61, 'Monday', '13.00', '2.50', 'IT ELEC 01', 'A'),
(4754, 32, 12, 61, 'Wednesday', '13.00', '2.50', 'IT ELEC 01', 'A'),
(4755, 32, 12, 63, 'Thursday', '9.00', '1.50', 'IT PC 213', 'A'),
(4756, 32, 12, 63, 'Saturday', '9.00', '1.50', 'IT PC 213', 'A'),
(4757, 32, 12, 64, 'Thursday', '14.00', '1.50', 'IT PC 211', 'A'),
(4758, 32, 12, 64, 'Saturday', '14.00', '1.50', 'IT PC 211', 'A'),
(4759, 32, 13, 67, 'Tuesday', '13.00', '2.50', 'CC100', 'A'),
(4760, 32, 13, 67, 'Friday', '13.00', '2.50', 'CC100', 'A'),
(4761, 32, 13, 68, 'Tuesday', '8.00', '2.50', 'CC101', 'A'),
(4762, 32, 13, 68, 'Friday', '8.00', '2.50', 'CC101', 'A');

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
-- Indexes for table `created_gened_schedules`
--
ALTER TABLE `created_gened_schedules`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_user_id` (`user_id`);

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
-- Indexes for table `final_allocations`
--
ALTER TABLE `final_allocations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `course_id` (`course_id`),
  ADD KEY `room_id` (`room_id`);

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
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=767;

--
-- AUTO_INCREMENT for table `classrooms`
--
ALTER TABLE `classrooms`
  MODIFY `room_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=29;

--
-- AUTO_INCREMENT for table `courses`
--
ALTER TABLE `courses`
  MODIFY `course_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=70;

--
-- AUTO_INCREMENT for table `created_gened_schedules`
--
ALTER TABLE `created_gened_schedules`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=146;

--
-- AUTO_INCREMENT for table `created_schedules`
--
ALTER TABLE `created_schedules`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=303;

--
-- AUTO_INCREMENT for table `faculties`
--
ALTER TABLE `faculties`
  MODIFY `faculty_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=46;

--
-- AUTO_INCREMENT for table `final_allocations`
--
ALTER TABLE `final_allocations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=228;

--
-- AUTO_INCREMENT for table `gened_courses`
--
ALTER TABLE `gened_courses`
  MODIFY `course_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=32;

--
-- AUTO_INCREMENT for table `gened_solutions`
--
ALTER TABLE `gened_solutions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=901;

--
-- AUTO_INCREMENT for table `programs`
--
ALTER TABLE `programs`
  MODIFY `program_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- AUTO_INCREMENT for table `room_courses`
--
ALTER TABLE `room_courses`
  MODIFY `course_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=321;

--
-- AUTO_INCREMENT for table `sections`
--
ALTER TABLE `sections`
  MODIFY `section_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `unavailable_times`
--
ALTER TABLE `unavailable_times`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=56;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=40;

--
-- AUTO_INCREMENT for table `user_solutions`
--
ALTER TABLE `user_solutions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4763;

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
-- Constraints for table `created_gened_schedules`
--
ALTER TABLE `created_gened_schedules`
  ADD CONSTRAINT `fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `created_schedules`
--
ALTER TABLE `created_schedules`
  ADD CONSTRAINT `created_schedules_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `final_allocations`
--
ALTER TABLE `final_allocations`
  ADD CONSTRAINT `final_allocations_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `room_courses` (`course_id`),
  ADD CONSTRAINT `final_allocations_ibfk_2` FOREIGN KEY (`room_id`) REFERENCES `classrooms` (`room_id`);

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
