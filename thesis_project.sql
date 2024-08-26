-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 23, 2024 at 07:19 AM
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
-- Table structure for table `courses`
--

CREATE TABLE `courses` (
  `course_id` int(11) NOT NULL,
  `course_code` varchar(255) NOT NULL,
  `course_name` varchar(255) NOT NULL,
  `course_block` varchar(50) DEFAULT NULL,
  `course_type` enum('Lecture','Comp Laboratory','Engineering Laboratory') NOT NULL,
  `course_level` enum('1st Year','2nd Year','3rd Year','4th Year') NOT NULL,
  `units` decimal(5,2) NOT NULL,
  `program_id` int(11) DEFAULT NULL,
  `faculty_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `courses`
--

INSERT INTO `courses` (`course_id`, `course_code`, `course_name`, `course_block`, `course_type`, `course_level`, `units`, `program_id`, `faculty_id`) VALUES
(21, 'CC103', 'DATA STRUCTURES AND ALGORITHMS', 'A', 'Lecture', '2nd Year', '3.00', 1, 12),
(22, 'CS PC 211', 'DISCRETE STRUCTURES 2', 'A', 'Lecture', '2nd Year', '3.00', 1, 13),
(23, 'CS PC 212', 'OBJECT ORIENTED PROGRAMMING', 'A', 'Comp Laboratory', '2nd Year', '3.00', 1, 12),
(24, 'CS PC ELEC 01', 'FUNDAMENTALS OF HUMAN COMPUTER INTERACTION', 'A', 'Comp Laboratory', '2nd Year', '3.00', 1, 14),
(25, 'MATH 100', 'CALCULUS', 'A', 'Lecture', '2nd Year', '3.00', 1, 15),
(26, 'CC103', 'DATA STRUCTURES AND ALGORITHMS', 'A', 'Lecture', '2nd Year', '3.00', 2, 12),
(27, 'IT ELEC 01', 'IT ELECTIVE 1', 'A', 'Comp Laboratory', '2nd Year', '3.00', 2, 16),
(28, 'IT PC 212', 'RELATED LEARNING EXPERIENCE', 'A', 'Lecture', '2nd Year', '1.00', 1, 12),
(29, 'IT PC 212', 'RELATED LEARNING EXPERIENCE', 'A', 'Lecture', '2nd Year', '1.00', 2, 12),
(30, 'IT PC 213', 'NETWORKING 1', 'A', 'Comp Laboratory', '2nd Year', '3.00', 2, 17),
(31, 'IT PC 211', 'INTRODUCTION TO HUMAN COMPUTER INTERACTION', 'A', 'Comp Laboratory', '2nd Year', '3.00', 2, 18);

-- --------------------------------------------------------

--
-- Table structure for table `faculty`
--

CREATE TABLE `faculty` (
  `faculty_id` int(11) NOT NULL,
  `first_name` varchar(255) NOT NULL,
  `last_name` varchar(255) NOT NULL,
  `faculty_type` enum('Full Time','Part Time') NOT NULL,
  `faculty_units` decimal(5,2) NOT NULL,
  `department` varchar(255) NOT NULL,
  `faculty_used_units` float NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `faculty`
--

INSERT INTO `faculty` (`faculty_id`, `first_name`, `last_name`, `faculty_type`, `faculty_units`, `department`, `faculty_used_units`) VALUES
(12, 'Mary Grace', 'Enriquez', 'Full Time', '25.00', 'SOECS', 11),
(13, 'Rhodora Faye', 'Brosas', 'Full Time', '25.00', 'SOECS', 3),
(14, 'Relian', 'Cadubla', 'Full Time', '25.00', 'SOECS', 3),
(15, 'Rey', 'Literal', 'Part Time', '18.00', 'SOECS', 3),
(16, 'Jp', 'Serrano', 'Full Time', '25.00', 'SOECS', 3),
(17, 'Jay ', 'Benaraba', 'Full Time', '25.00', 'SOECS', 3),
(18, 'Shaira', 'Pepeno', 'Full Time', '25.00', 'SOECS', 3);

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
(5, 'SEAS', 23);

-- --------------------------------------------------------

--
-- Table structure for table `sections`
--

CREATE TABLE `sections` (
  `section_id` int(11) NOT NULL,
  `section_name` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `department` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `sections`
--

INSERT INTO `sections` (`section_id`, `section_name`, `created_at`, `updated_at`, `department`) VALUES
(2, 'CS-2-A', '2024-08-14 07:02:07', '2024-08-14 07:02:07', 'SOECS'),
(3, 'IT-2-A', '2024-08-14 07:02:07', '2024-08-14 07:02:07', 'SOECS');

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
(3, 31);

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
(22, 2, 'Tuesday', '4.00', '5.50'),
(23, 2, 'Friday', '4.00', '5.50'),
(26, 3, 'Tuesday', '7.00', '8.50'),
(27, 3, 'Friday', '7.00', '8.50'),
(28, 3, 'Tuesday', '4.00', '5.50'),
(29, 3, 'Friday', '4.00', '5.50'),
(30, 3, 'Thursday', '1.00', '3.00'),
(31, 3, 'Monday', '3.00', '4.50'),
(32, 3, 'Wednesday', '3.00', '4.50');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `username` varchar(100) NOT NULL,
  `email` varchar(200) NOT NULL,
  `role` enum('registrar','dept-head','admin') NOT NULL,
  `department` enum('SOECS','SON','SBMA','SHOM','SEAS','REGISTRAR','ADMIN') NOT NULL,
  `password` varchar(200) NOT NULL,
  `is_verified` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `username`, `email`, `role`, `department`, `password`, `is_verified`) VALUES
(19, 'asd', '123@gmail.com', 'dept-head', 'SOECS', '$2b$12$acfLcf9yMjZgk5odNyKzButlj2QC.dTXwEQpWXCruJYr.4Qa7rSbW', 1),
(21, 'admin1', 'admin@gmail.com', 'admin', 'ADMIN', '$2b$12$AWe8tDr/KXM1HR0hecg8F.WPT92ugZ7rXwS41IXVJQYZfDQ.80m4W', 1),
(22, 'registrar', 'jkl@gmail.com', 'registrar', 'REGISTRAR', '$2b$12$ifjIP5Ceg6o7mH.rLpjKwujzkhnhLCoxlik5blvxyD7xiCxyQ6EQK', 0),
(23, 'seas', 'seas@gmail.com', 'dept-head', 'SEAS', '$2b$12$mzbySaSlcewM0xXwcvjMDOWyJ3jXfzM1YROeJj2xmaOR21OEh178.', 1);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`course_id`),
  ADD KEY `program_id` (`program_id`),
  ADD KEY `faculty_id` (`faculty_id`);

--
-- Indexes for table `faculty`
--
ALTER TABLE `faculty`
  ADD PRIMARY KEY (`faculty_id`);

--
-- Indexes for table `programs`
--
ALTER TABLE `programs`
  ADD PRIMARY KEY (`program_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `sections`
--
ALTER TABLE `sections`
  ADD PRIMARY KEY (`section_id`);

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
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `courses`
--
ALTER TABLE `courses`
  MODIFY `course_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=32;

--
-- AUTO_INCREMENT for table `faculty`
--
ALTER TABLE `faculty`
  MODIFY `faculty_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT for table `programs`
--
ALTER TABLE `programs`
  MODIFY `program_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `sections`
--
ALTER TABLE `sections`
  MODIFY `section_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `unavailable_times`
--
ALTER TABLE `unavailable_times`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=33;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `courses`
--
ALTER TABLE `courses`
  ADD CONSTRAINT `courses_ibfk_1` FOREIGN KEY (`program_id`) REFERENCES `programs` (`program_id`),
  ADD CONSTRAINT `courses_ibfk_2` FOREIGN KEY (`faculty_id`) REFERENCES `faculty` (`faculty_id`);

--
-- Constraints for table `programs`
--
ALTER TABLE `programs`
  ADD CONSTRAINT `programs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

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
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
