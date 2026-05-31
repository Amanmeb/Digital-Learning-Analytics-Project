FROM moodlehq/moodle-php-apache:8.1

# Install required PHP extensions and tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    unzip \
    libpng-dev \
    libzip-dev \
    libxml2-dev \
    && docker-php-ext-install zip xml soap \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Download Moodle 4.3
RUN curl -L https://download.moodle.org/download.php/direct/stable403/moodle-latest-403.tgz \
    -o /tmp/moodle.tgz \
    && tar -xzf /tmp/moodle.tgz -C /var/www/html --strip-components=1 \
    && rm /tmp/moodle.tgz

# Create moodledata directory
RUN mkdir -p /var/www/moodledata \
    && chown -R www-data:www-data /var/www/moodledata \
    && chown -R www-data:www-data /var/www/html

# Set permissions
RUN chmod -R 755 /var/www/html \
    && chmod -R 777 /var/www/moodledata

EXPOSE 80

CMD ["apache2-foreground"]
