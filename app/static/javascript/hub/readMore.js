document.querySelectorAll('.read-more').forEach(button => {
    button.addEventListener('click', function() {
        const description = this.closest('.project-text').querySelector('.project-description');
        const isHidden = description.style.display === 'none';
        
        description.style.display = isHidden ? 'block' : 'none';
        this.textContent = isHidden ? 'Read Less -' : 'Read More +';
    });
});