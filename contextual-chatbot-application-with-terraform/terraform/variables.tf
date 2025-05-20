variable "aws_region" {
  type    = string
  default = ""
}
variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default = "1"
}